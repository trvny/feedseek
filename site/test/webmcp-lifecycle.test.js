import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
test("WebMCP survives bfcache and aborts on real page exit", () => {
  const window = new EventTarget();
  const tools = [];
  const dummy = {};
  runInNewContext(readFileSync(new URL("../webmcp.js", import.meta.url), "utf8"), {
    document: {
      modelContext: { registerTool(tool, options) { tools.push({ tool, options }); } },
      querySelector(s) { return s === "#search" ? dummy : null; },
      querySelectorAll(s) { return s === ".card" ? [dummy] : []; },
    }, window, AbortController, console,
  });
  assert.equal(tools.length, 3);
  const cached = new Event("pagehide");
  cached.persisted = true;
  window.dispatchEvent(cached);
  assert.equal(tools[0].options.signal.aborted, false);
  window.dispatchEvent(new Event("pagehide"));
  assert.equal(tools[0].options.signal.aborted, true);
});

test("WebMCP catalog includes feeds outside the curated cards", async () => {
  const tools = [];
  const dummy = {};
  const catalog = {
    format: "feedseek-model-feed-catalog", version: 1,
    feeds: [{ key: "hidden-ai", title: "Hidden Żółć", feed_url: "https://example.com/ai.xml" }],
  };
  runInNewContext(readFileSync(new URL("../webmcp.js", import.meta.url), "utf8"), {
    document: {
      baseURI: "https://example.com/feedseek/",
      modelContext: { registerTool(tool) { tools.push(tool); } },
      querySelector(s) { return s === "#search" ? dummy : null; },
      querySelectorAll(s) { return s === ".card" ? [dummy] : []; },
    },
    window: new EventTarget(), AbortController, AbortSignal, URL, console,
    fetch: async (url) => {
      assert.equal(String(url), "https://example.com/feedseek/model-feeds.json");
      return new Response(JSON.stringify(catalog));
    },
  });
  const tool = tools.find((entry) => entry.name === "list_feeds");
  const found = await tool.execute({ query: "zolc", limit: 1 });
  assert.equal(found.count, 1);
  assert.equal(found.feeds[0].key, "hidden-ai");
  assert.equal(found.next_offset, null);
});
