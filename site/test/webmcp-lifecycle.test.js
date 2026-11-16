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
  assert.equal(tools.length, 2);
  const cached = new Event("pagehide");
  cached.persisted = true;
  window.dispatchEvent(cached);
  assert.equal(tools[0].options.signal.aborted, false);
  window.dispatchEvent(new Event("pagehide"));
  assert.equal(tools[0].options.signal.aborted, true);
});
