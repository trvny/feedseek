import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../reader-cache.js", import.meta.url), "utf8");

function memoryIndexedDB() {
  const records = new Map();
  const db = {
    objectStoreNames: { contains: () => false },
    createObjectStore() { return { createIndex() {} }; },
    close() {},
    transaction(_store, _mode) {
      const tx = {
        oncomplete: null, onabort: null, error: null,
        objectStore() {
          return {
            getAll() {
              const request = { result: null, onsuccess: null, onerror: null };
              queueMicrotask(() => {
                request.result = [...records.values()];
                request.onsuccess?.();
              });
              return request;
            },
            clear() {
              records.clear();
              queueMicrotask(() => tx.oncomplete?.());
            },
            put(row) { records.set(row.key, structuredClone(row)); },
          };
        },
      };
      return tx;
    },
  };
  return {
    open() {
      const request = { result: db, onsuccess: null, onerror: null, onupgradeneeded: null };
      queueMicrotask(() => {
        request.onupgradeneeded?.();
        request.onsuccess?.();
      });
      return request;
    },
    records,
  };
}

function makeCache(storage = new Map(), indexedDB = undefined) {
  const context = vm.createContext({
    window: { indexedDB },
    console,
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, value),
      removeItem: key => storage.delete(key),
    },
  });
  vm.runInContext(source, context);
  return { cache: context.window.FeedseekReaderCache, storage };
}

const entry = (id, ts, source = "Source") => ({
  id, ts, source, feedUrl: "https://example.test/feed", url: "https://example.test/" + id,
});

test("migrates the legacy snapshot into IndexedDB before deleting it", async () => {
  const db = memoryIndexedDB();
  const storage = new Map([["fs:snap", JSON.stringify({
    _v: 1, t: 123, items: [entry("a", 1), entry("b", 2)],
  })]]);
  const first = makeCache(storage, db).cache;
  assert.deepEqual(JSON.parse(JSON.stringify(await first.load())), [entry("a", 1), entry("b", 2)]);
  assert.equal(storage.has("fs:snap"), false);
  const second = makeCache(storage, db).cache;
  assert.deepEqual(JSON.parse(JSON.stringify(await second.load())), [entry("b", 2), entry("a", 1)]);
});

test("IndexedDB persists entries without localStorage snapshots", async () => {
  const db = memoryIndexedDB();
  const { cache, storage } = makeCache(new Map(), db);
  assert.equal(await cache.save([entry("a", 1), entry("b", 2)]), true);
  assert.equal(db.records.size, 2);
  assert.equal(storage.has("fs:snap"), false);
  assert.deepEqual(JSON.parse(JSON.stringify(await makeCache(storage, db).cache.load())),
    [entry("b", 2), entry("a", 1)]);
  await cache.save([entry("b", 3)]);
  assert.equal(db.records.size, 1);
});

test("unavailable IndexedDB falls back to quota-bounded legacy storage", async () => {
  const storage = new Map();
  const { cache } = makeCache(storage, { open() { throw new Error("disabled"); } });
  const many = Array.from({ length: 5100 }, (_, i) => entry(String(i), i));
  assert.equal(await cache.save(many), false);
  assert.equal(JSON.parse(storage.get("fs:snap")).items.length, 5000);
  assert.equal((await cache.load()).length, 5000);
});

test("history stays source-scoped and prefers fresh entry revisions", () => {
  const { cache } = makeCache();
  const feeds = [{ xmlUrl: "https://example.test/feed", title: "Source" }];
  const old = [entry("a", 1), entry("b", 2), entry("unsubscribed", 0, "Other")];
  const fresh = [entry("b", 4), entry("c", 5)];
  const merged = cache.mergeHistory(feeds, fresh, old);
  assert.deepEqual(JSON.parse(JSON.stringify(merged)), [entry("c", 5), entry("b", 4), entry("a", 1)]);
});

test("legacy same-origin feed_ URLs migrate to short names", async () => {
  const context = vm.createContext({
    window: {}, console, URL,
    location: { href: "https://trvny.github.io/feedseek/reader/" },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  });
  vm.runInContext(source, context);
  const canon = context.window.FeedseekReaderCache.canonicalFeedUrl;
  assert.equal(canon("https://trvny.github.io/feedseek/feed_wykop.xml"), "https://trvny.github.io/feedseek/wykop.xml");
  assert.equal(canon("https://trvny.github.io/feedseek/feed_wykop.json"), "https://trvny.github.io/feedseek/wykop.json");
  assert.equal(canon("https://other.example/feed_wykop.xml"), "https://other.example/feed_wykop.xml");
  assert.equal(canon("https://trvny.github.io/feedseek/wykop.xml"), "https://trvny.github.io/feedseek/wykop.xml");
  assert.equal(canon("https://trvny.github.io/other/feed_news.xml"), "https://trvny.github.io/other/feed_news.xml");
});
