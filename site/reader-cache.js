(() => {
  const DB_NAME = "feedseek-reader";
  const STORE = "entries";
  const DB_VERSION = 1;
  const SNAPSHOT_VERSION = 1;
  const MAX_STORED = 20000;
  const LEGACY_LIMIT = 5000;
  const LEGACY_KEY = "fs:snap";
  let dbPromise;
  let writeTail = Promise.resolve();

  function entryKey(item) {
    return JSON.stringify([
      item.feedUrl || item.source, item.source,
      item.id ? "id" : "url", item.id || item.url,
    ]);
  }

  // Legacy Feedseek Pages names feed_<key>.(xml|json) -> <key>.(xml|json).
  // Only inside the site root (parent of reader/), never other projects.
  function canonicalFeedUrl(url) {
    if (typeof url !== "string") return url;
    try {
      const root = new URL("../", globalThis.location?.href);
      const parsed = new URL(url);
      if (parsed.origin !== root.origin) return url;
      const match = parsed.pathname.match(/^(.*\/)feed_([^/]+\.(?:xml|json))$/);
      if (!match || match[1] !== root.pathname) return url;
      parsed.pathname = match[1] + match[2];
      return parsed.href;
    } catch { return url; }
  }

  function migrateItems(items) {
    return items.map(item => {
      const feedUrl = canonicalFeedUrl(item.feedUrl);
      return feedUrl === item.feedUrl ? item : { ...item, feedUrl };
    });
  }

  function isLocalGovplFeed(item) {
    if (!item.feedUrl && item.source === "Gov.pl") {
      return /^https:\/\/www\.gov\.pl\/web\//.test(String(item.url || item.id || ""));
    }
    try {
      const root = new URL("../", globalThis.location?.href);
      const url = new URL(item.feedUrl);
      return url.origin === root.origin
        && (url.pathname === root.pathname + "govpl_news.xml"
          || url.pathname === root.pathname + "feed_govpl_news.xml");
    } catch { return false; }
  }

  function omitFutureGovplNews(items) {
    const cutoff = Date.now() + 86400000;
    return items.filter(item => !isLocalGovplFeed(item) || !(Number(item.ts) > cutoff));
  }

  function byDate(a, b) {
    return (Number(b.ts) || 0) - (Number(a.ts) || 0);
  }

  function readLegacy() {
    try {
      const snap = JSON.parse(localStorage.getItem(LEGACY_KEY) || "null");
      return snap?._v === SNAPSHOT_VERSION && Array.isArray(snap.items) ? snap.items : [];
    } catch { return []; }
  }

  function writeLegacy(items) {
    if (!items.length) {
      try { localStorage.removeItem(LEGACY_KEY); } catch {}
      return;
    }
    const limit = Math.min(items.length, LEGACY_LIMIT);
    const write = count => {
      try {
        localStorage.setItem(LEGACY_KEY, JSON.stringify({
          _v: SNAPSHOT_VERSION, t: Date.now(), items: items.slice(0, count),
        }));
        return true;
      } catch { return false; }
    };
    if (write(limit)) return;
    let low = 1, high = limit - 1;
    while (low <= high) {
      const count = Math.floor((low + high) / 2);
      if (write(count)) low = count + 1;
      else high = count - 1;
    }
  }

  function clearLegacy() {
    try { localStorage.removeItem(LEGACY_KEY); } catch {}
  }

  function database() {
    if (!window.indexedDB) return Promise.resolve(null);
    if (!dbPromise) {
      dbPromise = new Promise(resolve => {
        let request;
        try { request = window.indexedDB.open(DB_NAME, DB_VERSION); }
        catch { resolve(null); return; }
        request.onupgradeneeded = () => {
          const db = request.result;
          if (!db.objectStoreNames.contains(STORE)) {
            const store = db.createObjectStore(STORE, { keyPath: "key" });
            store.createIndex("by_date", "ts");
          }
        };
        request.onsuccess = () => {
          const db = request.result;
          db.onversionchange = () => db.close();
          resolve(db);
        };
        request.onerror = () => resolve(null);
        request.onblocked = () => resolve(null);
      });
    }
    return dbPromise;
  }

  function readAll(db) {
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, "readonly").objectStore(STORE).getAll();
      request.onsuccess = () => resolve(request.result.map(row => row.item).sort(byDate));
      request.onerror = () => reject(request.error);
    });
  }

  function replaceEntries(db, items) {
    const snapshot = [...items].sort(byDate).slice(0, MAX_STORED);
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      tx.oncomplete = () => resolve();
      tx.onabort = () => reject(tx.error || new Error("IndexedDB transaction aborted"));
      tx.onerror = () => reject(tx.error || new Error("IndexedDB transaction failed"));
      const store = tx.objectStore(STORE);
      try {
        store.clear();
        for (const item of snapshot) {
          store.put({ key: entryKey(item), ts: Number(item.ts) || 0, item });
        }
      } catch (error) {
        tx.abort();
        reject(error);
      }
    });
  }

  async function loadRaw() {
    const legacy = readLegacy();
    const db = await database();
    if (!db) return legacy;
    try {
      const stored = await readAll(db);
      if (stored.length) {
        clearLegacy();
        return stored;
      }
      if (legacy.length) {
        await replaceEntries(db, legacy);
        clearLegacy();
      }
      return legacy;
    } catch (error) {
      console.warn("Reader cache load failed; using local snapshot", error);
      return legacy;
    }
  }

  async function load() {
    const migrated = migrateItems(await loadRaw());
    const items = omitFutureGovplNews(migrated);
    if (items.length !== migrated.length) await save(items);
    return items;
  }

  async function persist(items) {
    const db = await database();
    if (db) {
      try {
        await replaceEntries(db, items);
        clearLegacy();
        return true;
      } catch (error) {
        console.warn("Reader IndexedDB write failed; using local snapshot", error);
      }
    }
    writeLegacy(items);
    return false;
  }

  function save(items) {
    const snapshot = omitFutureGovplNews([...items]);
    const next = writeTail.then(() => persist(snapshot), () => persist(snapshot));
    writeTail = next.then(() => {}, () => {});
    return next;
  }

  function mergeHistory(feeds, fresh, previous) {
    fresh = omitFutureGovplNews(fresh);
    previous = omitFutureGovplNews(previous);
    const active = new Set(feeds.map(feed => JSON.stringify([feed.xmlUrl, feed.title])));
    const seen = new Set(fresh.map(entryKey));
    const history = [];
    for (const item of previous) {
      if (!active.has(JSON.stringify([item.feedUrl, item.source]))) continue;
      const key = entryKey(item);
      if (seen.has(key)) continue;
      seen.add(key);
      history.push(item);
    }
    history.sort(byDate);
    const slots = Math.max(0, MAX_STORED - fresh.length);
    return [...fresh, ...history.slice(0, slots)].sort(byDate);
  }

  window.FeedseekReaderCache = { load, save, mergeHistory, canonicalFeedUrl };
})();
