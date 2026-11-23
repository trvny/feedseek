import assert from "node:assert/strict";
import test from "node:test";
import app from "../src/app.js";

const BASE = "https://rss.bartek.lol";
const catalog = {
  format: "feedseek-model-feed-catalog",
  version: 1,
  feeds: [
    { key: "jbzd", title: "JBZD", description: "Memes", source_url: "https://jbzd.com.pl",
      feed_url: BASE + "/jbzd.xml", model_feed_url: BASE + "/jbzd.json", entry_count: 3, updated_at: null },
    { key: "openai", title: "OpenAI", description: "AI research", source_url: "https://openai.com",
      feed_url: BASE + "/openai.xml", model_feed_url: BASE + "/openai.json", entry_count: 1, updated_at: null },
  ],
};
const index = {
  indexed_from: "2026-11-20T10:00:00Z", truncated: false, skipped_feeds: [],
  items: [
    { id: "1", title: "Model update", summary: "New release", url: "https://openai.com/a",
      source_key: "openai", source: "OpenAI", text_kind: "summary",
      published_at: "2026-11-20T10:00:00Z", modified_at: null, tags: ["AI"] },
    { id: "2", title: "A meme", summary: "Laugh", url: "https://jbzd.com.pl/a",
      source_key: "jbzd", source: "JBZD", text_kind: "title",
      published_at: "2026-11-18T10:00:00Z", modified_at: null, tags: [] },
    { id: "3", title: "C language essentials", summary: "Low-level code", url: "https://example.com/c",
      source_key: "openai", source: "OpenAI", text_kind: "summary",
      published_at: "2026-11-19T10:00:00Z", modified_at: null, tags: ["C"] },
  ],
};
const model = {
  format: "feedseek-model-feed", source_key: "jbzd", title: "JBZD",
  items: [
    { id: "11", title: "First", text: "One", text_kind: "content",
      url: "https://jbzd.com.pl/11", date_published: "2026-11-20T10:00:00Z" },
    { id: "12", title: "Second", text: "x".repeat(2000), text_kind: "summary",
      url: "https://jbzd.com.pl/12", date_modified: "2026-11-21T10:00:00Z" },
    { id: "13", title: "Third", text: "Three", text_kind: "title", url: "https://jbzd.com.pl/13" },
  ],
};

async function withFetch(run, replies = { catalog, index, model }) {
  const original = globalThis.fetch;
  const fetched = [];
  globalThis.fetch = async (url) => {
    const uri = String(url);
    fetched.push(uri);
    const data = uri.endsWith("/model-feeds.json") ? replies.catalog
      : uri.endsWith("/feedseek-search-index.json") ? replies.index
        : uri.endsWith("/jbzd.json") ? replies.model : null;
    if (data === null) return new Response("Not found", { status: 404 });
    return Response.json(data);
  };
  try { await run(fetched); } finally { globalThis.fetch = original; }
}

const request = (path, init) => app.fetch(new Request(BASE + path, init));

test("GET /api/v1 explains the read-only endpoints without origin fetches", async () => {
  const result = await request("/api/v1");
  assert.equal(result.status, 200);
  assert.equal(result.headers.get("access-control-allow-origin"), "*");
  assert.equal(result.headers.get("x-robots-tag"), "noindex, follow");
  assert.deepEqual((await result.json()).routes, [
    "/api/v1/feeds", "/api/v1/recent", "/api/v1/feeds/{key}/items",
  ]);
});

test("catalog REST filter, pagination and canonical URLs reuse MCP catalog", async () => {
  await withFetch(async (requests) => {
    const response = await request("/api/v1/feeds?query=ai&limit=1&offset=0");
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("content-type"), "application/json; charset=utf-8");
    const json = await response.json();
    assert.equal(json.count, 1);
    assert.equal(json.next_offset, null);
    assert.equal(json.feeds[0].key, "openai");
    assert.equal(json.feeds[0].model_feed_url, BASE + "/openai.json");
    assert.equal(requests.length, 1);
  });
});

test("recent REST filters and caps compact data using the existing MCP index", async () => {
  await withFetch(async () => {
    const response = await request("/api/v1/recent?query=model&sources=openai&since=2026-11-19T00%3A00%3A00Z&limit=1");
    assert.equal(response.status, 200);
    const json = await response.json();
    assert.equal(json.count, 1);
    assert.equal(json.entries[0].source_key, "openai");
    assert.equal(json.truncated, false);
  });
});

test("history pagination includes snapshot and bounded excerpts", async () => {
  await withFetch(async (requests) => {
    const initial = await request("/api/v1/feeds/jbzd/items?limit=1");
    const first = await initial.json();
    assert.equal(first.total, 3);
    assert.match(first.snapshot, /^[0-9a-f]{64}$/);
    assert.equal(first.next_offset, 1);
    const response = await request("/api/v1/feeds/jbzd/items?limit=1&offset=1&snapshot=" + first.snapshot);
    assert.equal(response.status, 200);
    const json = await response.json();
    assert.equal(json.snapshot, first.snapshot);
    assert.equal(json.total, 3);
    assert.equal(json.next_offset, 2);
    assert.equal(json.items[0].id, "12");
    assert.equal(json.items[0].summary.length, 500);
    assert.equal(json.items[0].date_modified, "2026-11-21T10:00:00Z");
    assert.deepEqual(requests.map((x) => new URL(x).pathname), [
      "/feedseek/model-feeds.json", "/feedseek/jbzd.json",
      "/feedseek/model-feeds.json", "/feedseek/jbzd.json",
    ]);
  });
});

test("changed feed rejects stale snapshot with 409 and a restart hint", async () => {
  const mutable = { ...model, items: [...model.items] };
  await withFetch(async () => {
    const first = await (await request("/api/v1/feeds/jbzd/items?limit=1")).json();
    mutable.items.unshift({ id: "14", title: "New post", text: "Fresh", text_kind: "content" });
    const next = await request("/api/v1/feeds/jbzd/items?limit=1&offset=1&snapshot=" + first.snapshot);
    assert.equal(next.status, 409);
    assert.match((await next.json()).error, /restart pagination/);
  }, { catalog, index, model: mutable });
});

test("single-character topic and lowercase RFC 3339 cutoff work", async () => {
  await withFetch(async () => {
    const recent = await request("/api/v1/recent?query=C&since=2026-11-19t00%3A00%3A00z&limit=10");
    assert.equal(recent.status, 200);
    const rows = (await recent.json()).entries;
    assert.deepEqual(rows.map((row) => row.id), ["3"]);
  });
});

test("unknown feed returns 404 without attempting arbitrary origin URLs", async () => {
  await withFetch(async (requests) => {
    const response = await request("/api/v1/feeds/private/items");
    assert.equal(response.status, 404);
    assert.deepEqual(await response.json(), { error: "Unknown Feedseek source key" });
    assert.equal(requests.length, 1);
  });
});

test("HEAD, CORS preflight and method errors are consistent", async () => {
  const head = await request("/api/v1", { method: "HEAD" });
  assert.equal(head.status, 200);
  assert.equal(await head.text(), "");
  const preflight = await request("/api/v1/feeds", { method: "OPTIONS" });
  assert.equal(preflight.status, 204);
  assert.match(preflight.headers.get("access-control-allow-methods"), /HEAD/);
  const write = await request("/api/v1/recent", { method: "POST" });
  assert.equal(write.status, 405);
  assert.equal(write.headers.get("allow"), "GET, HEAD, OPTIONS");
  assert.equal((await write.json()).error, "Method not allowed");
});

test("invalid and repeated query parameters fail closed", async () => {
  for (const path of [
    "/api/v1/feeds?limit=0", "/api/v1/feeds?offset=-1",
    "/api/v1/feeds?limit=2&limit=3", "/api/v1/feeds?ignored=1",
    "/api/v1/recent?since=yesterday", "/api/v1/recent?sources=a,,b",
    "/api/v1/recent?limit=101", "/api/v1/feeds/jbzd/items?limit=51",
    "/api/v1/feeds/jbzd/items?offset=1",
    "/api/v1/feeds/jbzd/items?offset=1&snapshot=abc",
  ]) {
    const response = await request(path);
    assert.equal(response.status, 400, path);
    assert.equal(response.headers.get("cache-control"), "no-store");
  }
});

test("upstream outage returns 503 JSON rather than success or empty catalog", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw Error("Connection reset"); };
  try {
    const response = await request("/api/v1/feeds?limit=20");
    assert.equal(response.status, 503);
    assert.equal((await response.json()).error, "Feedseek upstream temporarily unavailable");
  } finally {
    globalThis.fetch = original;
  }
});

test("REST also works on the legacy Worker hostname", async () => {
  const response = await app.fetch(new Request("https://feeds-proxy.travny.workers.dev/api/v1"));
  assert.equal(response.status, 200);
  assert.equal((await response.json()).version, "1");
});
