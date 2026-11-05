import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const reader = await readFile(new URL("../reader.js", import.meta.url), "utf8");
const utils = await readFile(new URL("../reader-fetch.js", import.meta.url), "utf8");
const cache = await readFile(new URL("../reader-cache.js", import.meta.url), "utf8");

class Element {
  children = [];
  style = {};
  dataset = {};
  textContent = "";
  value = "";
  constructor(tagName) { this.tagName = tagName; }
  get childNodes() { return this.children; }
  appendChild(child) {
    if (child.tagName === "fragment") this.children.push(...child.children);
    else this.children.push(child);
  }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  setAttribute() {}
  removeAttribute() {}
  focus() { this.focused = true; }
  closest(selector) { return selector === `.${this.className}` ? this : null; }
}

async function makeReader(feeds, entries, snapshotQuota = Infinity, initialStorage = null) {
  const nodes = new Map();
  const storage = initialStorage || new Map([["fs:cfg", JSON.stringify({ favs: false, thumbs: false })]]);
  const listeners = {};
  const document = {
    baseURI: "https://reader.test/reader/",
    querySelector(selector) {
      if (!nodes.has(selector)) nodes.set(selector, new Element("div"));
      return nodes.get(selector);
    },
    querySelectorAll(selector) {
      return selector === "#list .item"
        ? nodes.get("#list").children.filter(n => n.className === "item") : [];
    },
    createElement: tag => new Element(tag),
    createTextNode: text => ({ textContent: text }),
    createDocumentFragment: () => new Element("fragment"),
    addEventListener: (name, handler) => { listeners[name] = handler; },
  };
  const opml = `<opml><body>${feeds.map(f =>
    `<outline title="${f.title}" xmlUrl="${f.xmlUrl}"/>`
  ).join("")}</body></opml>`;
  const window = { fetch: async () => new Response(opml) };
  const context = vm.createContext({
    document, window, URL, Request, TextDecoder, AbortController, setTimeout, clearTimeout, console,
    location: { origin: "https://reader.test" },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => {
        if (key === "fs:snap" && JSON.parse(value).items.length > snapshotQuota) {
          throw new Error("Quota exceeded");
        }
        storage.set(key, value);
      },
      removeItem: key => storage.delete(key),
    },
  });
  context.fetch = (...args) => window.fetch(...args);
  vm.runInContext(utils, context);
  vm.runInContext(cache, context);
  vm.runInContext(reader, context);
  context.loadFeed = async feed => entries.get(feed.xmlUrl);
  await vm.runInContext("startupPromise", context);
  const articles = () => nodes.get("#list").children.filter(n => n.className === "item");
  const click = element => listeners.click({ target: element });
  const filter = source => {
    const chip = new Element("button");
    chip.className = "chip";
    chip.dataset.source = source;
    if (source === "All") chip.dataset.all = "true";
    click(chip);
  };
  return { context, storage, nodes, articles, click, filter };
}

function fixture(counts) {
  const feeds = [], entries = new Map();
  counts.forEach((count, source) => {
    const feed = { title: `Source ${source}`, xmlUrl: `https://feed.test/${source}.xml` };
    feeds.push(feed);
    entries.set(feed.xmlUrl, Array.from({ length: count }, (_, i) => ({
      id: `entry-${source}-${i}`,
      source: feed.title, feedUrl: feed.xmlUrl, title: `Article ${source}/${i}`,
      url: `https://article.test/${source}/${i}`, ts: source * 10000 + i,
    })));
  });
  return { feeds, entries };
}

test("refresh retains and snapshots all sources before filtering and pagination", async () => {
  const { feeds, entries } = fixture(Array(110).fill(10));
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 1100);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 1100);
  assert.equal(r.articles().length, 250);
  assert.match(r.nodes.get("#count").textContent, /^250 of 1100 items/);

  r.filter("Source 0");
  assert.equal(r.articles().length, 10);
  assert.equal(r.articles()[0].href, "https://article.test/0/9");
  assert.match(r.nodes.get("#count").textContent, /^10 items/);
});

test("source search narrows chips without changing subscriptions or the selected source", async () => {
  const { feeds, entries } = fixture([2, 3, 4]);
  const r = await makeReader(feeds, entries);
  r.filter("Source 0");
  const search = r.nodes.get("#sourceSearch");
  search.value = "source 2";
  search.oninput();
  const chips = r.nodes.get("#chips").children;
  assert.deepEqual(chips.filter(row => !row.hidden).map(row => row.dataset.source), ["All", "Source 0", "Source 2"]);
  assert.equal(r.articles().length, 2);
  r.filter("Source 2");
  assert.equal(r.articles().length, 4);
  assert.equal(vm.runInContext("FEEDS.length", r.context), 3);
  search.value = "";
  search.oninput();
  assert.equal(r.nodes.get("#chips").children.filter(chip => !chip.hidden).length, 4);
});

test("pinned sources stay first after reload without changing subscriptions or the selected source", async () => {
  const { feeds, entries } = fixture([2, 3, 4]);
  const r = await makeReader(feeds, entries);
  r.filter("Source 0");
  const source2 = r.nodes.get("#chips").children.find(row => row.dataset.source === "Source 2");
  r.click(source2.children[1]);
  assert.deepEqual(r.nodes.get("#chips").children.map(row => row.dataset.source), ["All", "Source 2", "Source 0", "Source 1"]);
  assert.equal(r.articles().length, 2);
  assert.equal(vm.runInContext("FEEDS.length", r.context), 3);
  assert.deepEqual(JSON.parse(r.storage.get("fs:sourceFavorites")), [feeds[2].xmlUrl]);
  const reloaded = await makeReader(feeds, entries, Infinity, r.storage);
  assert.equal(reloaded.nodes.get("#chips").children[1].dataset.source, "Source 2");
  reloaded.click(reloaded.nodes.get("#chips").children[1].children[1]);
  assert.deepEqual(JSON.parse(reloaded.storage.get("fs:sourceFavorites")), []);
});

test("pin survives source rename and migrates existing name-based favorites", async () => {
  const { feeds, entries } = fixture([1, 1]);
  const storage = new Map([["fs:cfg", JSON.stringify({ favs: false, thumbs: false })], ["fs:sourceFavorites", JSON.stringify(["Source 1"])]]);
  const first = await makeReader(feeds, entries, Infinity, storage);
  assert.equal(first.nodes.get("#chips").children[1].dataset.source, "Source 1");
  assert.deepEqual(JSON.parse(storage.get("fs:sourceFavorites")), [feeds[1].xmlUrl]);
  feeds[1].title = "Renamed source";
  entries.get(feeds[1].xmlUrl).forEach(item => { item.source = feeds[1].title; });
  const reloaded = await makeReader(feeds, entries, Infinity, storage);
  assert.equal(reloaded.nodes.get("#chips").children[1].dataset.source, "Renamed source");
  assert.equal(reloaded.nodes.get("#chips").children[1].children[1].textContent, "★");
});

test("legacy name-based favorites migrate for feeds with no current items", async () => {
  const { feeds, entries } = fixture([1, 1]);
  entries.set(feeds[1].xmlUrl, []);
  const storage = new Map([["fs:cfg", JSON.stringify({ favs: false, thumbs: false })], ["fs:sourceFavorites", JSON.stringify(["Source 1"])]]);
  await makeReader(feeds, entries, Infinity, storage);
  assert.deepEqual(JSON.parse(storage.get("fs:sourceFavorites")), [feeds[1].xmlUrl]);
  feeds[1].title = "Renamed source";
  entries.set(feeds[1].xmlUrl, [{
    id: "entry-1-0", source: feeds[1].title, feedUrl: feeds[1].xmlUrl, title: "Article 1/0",
    url: "https://article.test/1/0", ts: 10000,
  }]);
  const reloaded = await makeReader(feeds, entries, Infinity, storage);
  assert.equal(reloaded.nodes.get("#chips").children[1].dataset.source, "Renamed source");
  assert.equal(reloaded.nodes.get("#chips").children[1].children[1].textContent, "★");
});

test("failed pin writes leave the previous selection intact and show an error", async () => {
  const { feeds, entries } = fixture([1, 1]);
  const reader = await makeReader(feeds, entries);
  reader.filter("Source 0");
  const setItem = reader.context.localStorage.setItem;
  reader.context.localStorage.setItem = (key, value) => {
    if (key === "fs:sourceFavorites") throw new Error("Quota exceeded");
    setItem(key, value);
  };
  reader.click(reader.nodes.get("#chips").children[2].children[1]);
  assert.equal(reader.nodes.get("#chips").children[2].children[1].textContent, "☆");
  assert.equal(reader.nodes.get("#sourceSelection").textContent, "Source 0");
  assert.equal(reader.articles().length, 1);
  assert.match(reader.nodes.get("#sourceError").textContent, /Could not save/);
  assert.equal(reader.storage.has("fs:sourceFavorites"), false);
  reader.context.localStorage.setItem = setItem;
  reader.click(reader.nodes.get("#chips").children[2].children[1]);
  assert.equal(reader.nodes.get("#sourceError").textContent, "");
  assert.deepEqual(JSON.parse(reader.storage.get("fs:sourceFavorites")), [feeds[1].xmlUrl]);
});

test("a source named All is distinct from the All filter and can be pinned", async () => {
  const { feeds, entries } = fixture([2, 1]);
  feeds[0].title = "All";
  entries.get(feeds[0].xmlUrl).forEach(item => { item.source = "All"; });
  const reader = await makeReader(feeds, entries);
  const allSource = reader.nodes.get("#chips").children.find(row => row.dataset.source === "All" && !row.dataset.all);
  assert.equal(allSource.children[0].textContent, "All (source)");
  reader.click(allSource.children[1]);
  assert.deepEqual(JSON.parse(reader.storage.get("fs:sourceFavorites")), [feeds[0].xmlUrl]);
  const pinned = reader.nodes.get("#chips").children.find(row => row.dataset.source === "All" && !row.dataset.all);
  reader.click(pinned.children[0]);
  assert.equal(reader.articles().length, 2);
  assert.equal(reader.nodes.get("#sourceSelection").textContent, "All (source)");
  reader.click(reader.nodes.get("#chips").children[0].children[0]);
  assert.equal(reader.articles().length, 3);
});

test("shared page URLs keep distinct entry IDs and independent source memberships", async () => {
  const { feeds, entries } = fixture([3, 1]);
  const first = entries.get(feeds[0].xmlUrl);
  first.forEach(item => { item.url = "https://article.test/changelog"; });
  first[2].id = first[0].id;
  const other = entries.get(feeds[1].xmlUrl)[0];
  other.url = first[0].url;
  other.id = first[0].id;
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 3);
  r.filter("Source 0");
  assert.equal(r.articles().length, 2);
  r.filter("Source 1");
  assert.equal(r.articles().length, 1);
});

test("subscription aliases and explicit IDs remain distinct from URL fallbacks", async () => {
  const { feeds, entries } = fixture([3]);
  const items = entries.get(feeds[0].xmlUrl);
  items[0].id = "https://article.test/fallback";
  items[0].url = "https://article.test/explicit";
  items[1].id = "";
  items[1].url = items[0].id;
  items[2].id = "last";
  feeds.push({ ...feeds[0], title: "Alias" });
  const r = await makeReader(feeds, entries);
  r.context.loadFeed = async feed => items.map(item => ({ ...item, source: feed.title }));
  await vm.runInContext("run()", r.context);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 6);
  r.filter("Alias");
  assert.equal(r.articles().length, 3);
});

test("Atom IDs and RSS GUIDs survive parsing when entries reuse a page URL", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  for (const [rootName, idTag] of [["feed", "id"], ["rss", "guid"]]) {
    r.context.DOMParser = class {
      parseFromString() {
        return {
          documentElement: { tagName: rootName, children: [] },
          querySelector: () => null,
          querySelectorAll: () => ["first", "second"].map(id => ({
            children: [
              { tagName: idTag, textContent: id },
              { tagName: "title", textContent: id },
              { tagName: "link", textContent: "https://article.test/changelog", getAttribute: () => null },
            ],
            getElementsByTagName: () => [],
          })),
        };
      }
    };
    const parsed = vm.runInContext('parseFeed("xml", "Feed", "https://feed.test/feed")', r.context);
    assert.deepEqual(Array.from(parsed, item => item.id), ["first", "second"]);
    assert.equal(parsed[0].url, parsed[1].url);
  }
});

test("publication dates take precedence over update dates regardless of XML order", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  r.context.DOMParser = class {
    parseFromString() {
      return {
        documentElement: { tagName: "feed", children: [] },
        querySelector: () => null,
        querySelectorAll: () => [{
          children: [
            { tagName: "updated", textContent: "2026-11-01T12:00:00Z" },
            { tagName: "published", textContent: "2026-10-01T12:00:00Z" },
            { tagName: "title", textContent: "Article" },
            { tagName: "link", textContent: "https://article.test/story", getAttribute: () => null },
          ],
          getElementsByTagName: () => [],
        }],
      };
    }
  };
  const parsed = vm.runInContext('parseFeed("xml", "Feed", "https://feed.test/feed")', r.context);
  assert.equal(parsed[0].ts, Date.parse("2026-10-01T12:00:00Z"));
});

test("a dc:date takes precedence over an updated timestamp", async () => {
  const { feeds, entries } = fixture([1]);
  const reader = await makeReader(feeds, entries);
  reader.context.DOMParser = class {
    parseFromString() {
      return {
        documentElement: { tagName: "feed", children: [] },
        querySelector: () => null,
        querySelectorAll: () => [{
          children: [
            { tagName: "updated", textContent: "2026-11-01T12:00:00Z" },
            { tagName: "dc:date", textContent: "2026-10-01T12:00:00Z" },
            { tagName: "title", textContent: "Article" },
            { tagName: "link", textContent: "https://article.test/story", getAttribute: () => null },
          ],
          getElementsByTagName: () => [],
        }],
      };
    }
  };
  const parsed = vm.runInContext('parseFeed("xml", "Feed", "https://feed.test/feed")', reader.context);
  assert.equal(parsed[0].ts, Date.parse("2026-10-01T12:00:00Z"));
});

test("invalid dates fall back to the first parseable timestamp", async () => {
  const { feeds, entries } = fixture([1]);
  const reader = await makeReader(feeds, entries);
  reader.context.DOMParser = class {
    parseFromString() {
      return {
        documentElement: { tagName: "feed", children: [] },
        querySelector: () => null,
        querySelectorAll: () => [{
          children: [
            { tagName: "published", textContent: "invalid date" },
            { tagName: "dc:date", textContent: "also invalid" },
            { tagName: "updated", textContent: "2026-11-01T12:00:00Z" },
            { tagName: "title", textContent: "Article" },
            { tagName: "link", textContent: "https://article.test/story", getAttribute: () => null },
          ],
          getElementsByTagName: () => [],
        }, {
          children: [
            { tagName: "published", textContent: "invalid date" },
            { tagName: "updated", textContent: "also invalid" },
            { tagName: "title", textContent: "Undated article" },
            { tagName: "link", textContent: "https://article.test/undated", getAttribute: () => null },
          ],
          getElementsByTagName: () => [],
        }],
      };
    }
  };
  const parsed = vm.runInContext('parseFeed("xml", "Feed", "https://feed.test/feed")', reader.context);
  assert.equal(parsed[0].ts, Date.parse("2026-11-01T12:00:00Z"));
  assert.equal(parsed[1].ts, 0);
});

test("future dates display their actual date instead of a false one-minute age", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  const future = Date.now() + 30 * 86400000;
  assert.equal(r.context.rel(future), new Date(future).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }));
});

test("Show more reaches the complete source and resets on source changes and refresh", async () => {
  const { feeds, entries } = fixture([600, 10]);
  const r = await makeReader(feeds, entries);
  r.filter("Source 0");
  const more = () => r.nodes.get("#list").children.find(n => n.className === "load-more");
  assert.equal(r.articles().length, 250);
  r.click(more());
  assert.equal(r.articles().length, 500);
  assert.equal(r.articles()[250].focused, true);
  r.filter("Source 0");
  assert.equal(r.articles().length, 500);
  assert.equal(more().textContent, "Show 100 more");
  r.click(more());
  assert.equal(r.articles().length, 600);
  assert.equal(more(), undefined);
  assert.equal(r.articles().at(-1).href, "https://article.test/0/0");
  assert.equal(r.articles()[500].focused, true);

  r.filter("All");
  assert.equal(r.articles().length, 250);
  r.click(more());
  await vm.runInContext("run()", r.context);
  assert.equal(r.articles().length, 250);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 610);
});

test("a failed refresh preserves cached source entries beyond the first display page", async () => {
  const { feeds, entries } = fixture([600, 10]);
  const r = await makeReader(feeds, entries);
  r.context.loadFeed = async feed => {
    if (feed.xmlUrl === feeds[0].xmlUrl) throw new Error("offline");
    return entries.get(feed.xmlUrl);
  };
  await vm.runInContext("run()", r.context);
  r.filter("Source 0");
  assert.equal(vm.runInContext("ITEMS.filter(i => i.source === FILTER).length", r.context), 600);
  assert.match(r.nodes.get("#count").textContent, /^250 of 600 items.*1 failed/);
});

test("offline snapshot bounds do not discard loaded source history", async () => {
  const { feeds, entries } = fixture([6000]);
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 6000);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 5000);
});

test("quota-limited snapshots retain the largest fitting prefix", async () => {
  const { feeds, entries } = fixture([1100]);
  const r = await makeReader(feeds, entries, 250);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 250);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 1100);
});

test("oversized entry lists fail before materializing individual articles", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  r.context.DOMParser = class {
    parseFromString() {
      return {
        documentElement: { tagName: "rss", children: [] },
        querySelector: () => null,
        querySelectorAll: () => ({ length: 10001 }),
      };
    }
  };
  assert.throws(
    () => vm.runInContext('parseFeed("xml", "Large", "https://feed.test/large")', r.context),
    /entry limit/,
  );
});

test("refresh retains earlier articles from subscribed sources", async () => {
  const { feeds, entries } = fixture([3, 1]);
  const r = await makeReader(feeds, entries);
  const old = entries.get(feeds[0].xmlUrl);
  entries.set(feeds[0].xmlUrl, [{ ...old[2], id: "newer", title: "Newer", ts: 20000 }]);
  await vm.runInContext("run()", r.context);
  r.filter("Source 0");
  assert.equal(r.articles().length, 4);
  assert.equal(vm.runInContext("ITEMS.filter(i => i.source === 'Source 0').length", r.context), 4);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 5);
});

test("unsubscribed sources are excluded from retained history", async () => {
  const { feeds, entries } = fixture([2, 2]);
  const r = await makeReader(feeds, entries);
  vm.runInContext("overlay.removed.push('https://feed.test/0.xml')", r.context);
  await vm.runInContext("run()", r.context);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 2);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 2);
});
