const { test } = require("node:test");
const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { runInNewContext } = require("node:vm");
test("WebMCP survives bfcache and aborts on real page exit", () => {
  const window = new EventTarget();
  const tools = [];
  const dummy = {};
  runInNewContext(readFileSync(join(__dirname, "../webmcp.js"), "utf8"), {
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
