import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const source = await readFile(new URL("../reader-fetch.js", import.meta.url), "utf8");

function makeContext(nativeFetch, cfg = {}) {
  const window = { fetch: nativeFetch };
  const context = vm.createContext({
    Request,
    URL,
    document: { baseURI: "https://reader.test/reader.html" },
    location: { origin: "https://reader.test" },
    localStorage: { getItem: key => key === "fs:cfg" ? JSON.stringify(cfg) : null },
    window,
  });
  vm.runInContext(source, context);
  return window;
}

test("limits feed tasks while preserving input order", async () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { allSettledLimited } = window.FeedseekReaderUtils;
  let active = 0;
  let maxActive = 0;

  const results = await allSettledLimited(Array.from({ length: 30 }, (_, i) => i), 12, async item => {
    active += 1;
    maxActive = Math.max(maxActive, active);
    await new Promise(resolve => setTimeout(resolve, 5));
    active -= 1;
    return item * 2;
  });

  assert.equal(maxActive, 12);
  assert.equal(results.length, 30);
  results.forEach((result, index) => {
    assert.equal(result.status, "fulfilled");
    assert.equal(result.value, index * 2);
  });
});

test("does not start queued tasks until a worker slot is free", async () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { allSettledLimited } = window.FeedseekReaderUtils;
  const releases = [];
  const started = [];

  const run = allSettledLimited([0, 1, 2], 2, async item => {
    started.push(item);
    if (item < 2) await new Promise(resolve => releases.push(resolve));
    return item;
  });

  await new Promise(resolve => setTimeout(resolve, 0));
  assert.deepEqual(started, [0, 1]);
  releases.shift()();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.deepEqual(started, [0, 1, 2]);
  releases.shift()();
  await run;
});

test("preserves rejected results without stopping other tasks", async () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { allSettledLimited } = window.FeedseekReaderUtils;
  const boom = new Error("boom");

  const results = await allSettledLimited(["a", "b", "c"], 2, async item => {
    if (item === "b") throw boom;
    return item.toUpperCase();
  });

  assert.equal(results[0].status, "fulfilled");
  assert.equal(results[0].value, "A");
  assert.equal(results[1].status, "rejected");
  assert.equal(results[1].reason, boom);
  assert.equal(results[2].status, "fulfilled");
  assert.equal(results[2].value, "C");
});



test("reader favicon candidates prefer explicit feed assets, then managed resolver", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { faviconCandidates } = window.FeedseekReaderUtils;

  const wykop = Array.from(faviconCandidates(
    "https://wykop.pl/static/img/favicons/favicon.png",
    "https://wykop.pl/",
    32,
  ));
  assert.equal(wykop[0], "https://wykop.pl/static/img/favicons/favicon.png");
  assert.match(wykop[1], /^https:\/\/feeds\.trfny\.com\/favicon\?/);
  assert.match(wykop[1], /domain=wykop\.pl/);

  const newsify = Array.from(faviconCandidates(
    "https://newsify.today/favicon.ico",
    "https://newsify.today/polish/PL",
    32,
  ));
  assert.match(newsify[0], /^https:\/\/feeds\.trfny\.com\/favicon\?/);
  assert.equal(newsify.at(-1), "https://newsify.today/favicon.ico");
});

test("reader favicon candidates keep already managed feed icons first", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { faviconCandidates } = window.FeedseekReaderUtils;
  const managed = "https://feeds.trfny.com/favicon?domain=jbzd.com.pl&sz=64";

  const candidates = Array.from(faviconCandidates(
    managed,
    "https://jbzd.com.pl/",
    32,
  ));

  assert.equal(candidates[0], managed);
  assert.match(candidates[1], /domain=jbzd\.com\.pl/);
  assert.match(candidates[1], /sz=32/);
});

test("keeps same-origin proxy bypass unchanged", async () => {
  const seen = [];
  const nativeFetch = input => {
    seen.push(String(input));
    return Promise.resolve(new Response("ok"));
  };
  const proxy = "https://proxy.test/?url=";
  const window = makeContext(nativeFetch, { proxy });
  const target = "https://reader.test/feed.xml";

  await window.fetch(proxy + encodeURIComponent(target));

  assert.deepEqual(seen, [target]);
});


test("keeps cached items only for feeds that failed", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { mergeRefreshResults } = window.FeedseekReaderUtils;
  const feeds = [
    { title: "Same title", xmlUrl: "https://a.test/feed", htmlUrl: "https://a.test/" },
    { title: "Same title", xmlUrl: "https://b.test/feed", htmlUrl: "https://b.test/" },
  ];
  const fresh = { source: "Same title", feedUrl: feeds[0].xmlUrl, url: "https://a.test/new" };
  const staleA = { source: "Same title", feedUrl: feeds[0].xmlUrl, url: "https://a.test/old" };
  const staleB = { source: "Old title", feedUrl: feeds[1].xmlUrl, url: "https://b.test/old" };
  const results = [
    { status: "fulfilled", value: [fresh] },
    { status: "rejected", reason: new Error("down") },
  ];

  const merged = mergeRefreshResults(feeds, results, [staleA, staleB]);

  assert.deepEqual(Array.from(merged.failed), ["Same title"]);
  assert.equal(merged.items.length, 2);
  assert.equal(merged.items[0].url, fresh.url);
  assert.equal(merged.items[1].url, staleB.url);
  assert.equal(merged.items[1].source, "Same title");
});

test("does not keep cached items for unsubscribed feeds", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { mergeRefreshResults } = window.FeedseekReaderUtils;
  const feed = { title: "Current", xmlUrl: "https://current.test/feed" };
  const removed = { source: "Removed", feedUrl: "https://removed.test/feed", url: "https://removed.test/old" };

  const merged = mergeRefreshResults(
    [feed],
    [{ status: "rejected", reason: new Error("down") }],
    [removed],
  );

  assert.equal(merged.items.length, 0);
  assert.deepEqual(Array.from(merged.failed), ["Current"]);
});


test("migrates legacy cached items to a unique feed URL before preserving them", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { mergeRefreshResults } = window.FeedseekReaderUtils;
  const feed = { title: "Legacy", xmlUrl: "https://legacy.test/feed" };
  const cached = { source: "Legacy", url: "https://legacy.test/article" };

  const merged = mergeRefreshResults(
    [feed],
    [{ status: "rejected", reason: new Error("down") }],
    [cached],
  );

  assert.equal(merged.items.length, 1);
  assert.equal(merged.items[0].feedUrl, feed.xmlUrl);
  assert.equal(merged.items[0].url, cached.url);
});


test("legacy cached items inherit the OPML site URL for favicon fallback", () => {
  const window = makeContext(() => Promise.resolve(new Response("ok")));
  const { mergeRefreshResults } = window.FeedseekReaderUtils;
  const feed = {
    title: "Legacy",
    xmlUrl: "https://reader.test/feed_legacy.xml",
    htmlUrl: "https://legacy.example/news",
  };
  const cached = { source: "Legacy", url: "https://other.example/article" };

  const merged = mergeRefreshResults(
    [feed],
    [{ status: "rejected", reason: new Error("down") }],
    [cached],
  );

  assert.equal(merged.items[0].feedUrl, feed.xmlUrl);
  assert.equal(merged.items[0].feedSite, feed.htmlUrl);
});
