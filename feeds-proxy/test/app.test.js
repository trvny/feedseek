import assert from "node:assert/strict";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { unstable_readConfig } from "wrangler";

import app from "../src/app.js";

const challengeUrl = "https://feeds.trfny.com/.well-known/openai-apps-challenge";

test("serves the OpenAI domain verification token as plain text", async () => {
  const response = await app.fetch(new Request(challengeUrl), {
    OPENAI_APPS_CHALLENGE: "challenge-token-123",
  });

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "text/plain; charset=utf-8");
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(await response.text(), "challenge-token-123");
});

test("serves verification on the canonical Feedseek MCP hostname", async () => {
  const ctx = { exports: {
    FeedseekSite: { fetch() { throw Error("Verification must not hit Pages"); } },
    FeedseekProxy: { fetch() { throw Error("Verification must not hit proxy"); } },
  } };
  const response = await app.fetch(new Request("https://rss.bartek.lol/.well-known/openai-apps-challenge"),
    { OPENAI_APPS_CHALLENGE: "canonical-token" }, ctx);
  assert.equal(response.status, 200);
  assert.equal(await response.text(), "canonical-token");
});

test("keeps the verification endpoint closed until a token is configured", async () => {
  const response = await app.fetch(new Request(challengeUrl), {});
  assert.equal(response.status, 404);
});

test("rejects write methods on the verification endpoint", async () => {
  const response = await app.fetch(
    new Request(challengeUrl, { method: "POST" }),
    { OPENAI_APPS_CHALLENGE: "challenge-token-123" },
  );

  assert.equal(response.status, 405);
  assert.equal(response.headers.get("allow"), "GET, HEAD");
});

test("routes WebSub topic requests around the cached subworker", async () => {
  const ctx = { exports: {
    FeedseekSite: { fetch() { throw Error("Cached site entrypoint must not receive WebSub topics"); } },
    FeedseekProxy: { fetch() { throw Error("Wrong proxy"); } },
  } };
  const result = await app.fetch(new Request("https://rss.bartek.lol/jbzd.xml"), {}, ctx);
  // The real upstream may be unavailable in isolated Node tests, but it must
  // not reach either of the cached WorkerEntrypoints.
  assert.ok([200, 502].includes(result.status));
});

test("serves remote MCP on both the public and legacy Worker domains", async () => {
  const ctx = { exports: {
    FeedseekSite: { fetch: () => { throw new Error("MCP must not hit Pages"); } },
    FeedseekProxy: { fetch: () => { throw new Error("MCP must not hit proxy"); } },
  } };
  for (const hostname of ["rss.bartek.lol", "feeds-proxy.travny.workers.dev"]) {
    const response = await app.fetch(new Request(`https://${hostname}/mcp`, {
      method: "POST",
      headers: {"content-type":"application/json"},
      body: JSON.stringify({jsonrpc:"2.0",id:1,method:"ping"}),
    }), {}, ctx);
    assert.equal(response.status, 200);
    assert.ok((await response.json()).result);
  }
});

test("routes the same path on each hostname to separate cache entrypoints", async () => {
  const configPath = fileURLToPath(new URL("../wrangler.jsonc", import.meta.url));
  const config = unstable_readConfig({ config: configPath });
  assert.equal(config.exports.default?.cache?.enabled ?? config.cache.enabled, false);

  const ctx = { exports: {
    FeedseekSite: { fetch: () => new Response("Allow: /") },
    FeedseekProxy: { fetch: () => new Response("Disallow: /") },
  } };
  for (const name of Object.keys(ctx.exports)) {
    assert.equal(config.exports[name]?.cache?.enabled, true, name);
  }

  const inputs = [
    ["rss.bartek.lol", "Allow: /"],
    ["feeds-proxy.travny.workers.dev", "Disallow: /"],
  ];
  for (const [host, policy] of inputs) {
    const result = await app.fetch(new Request(`https://${host}/robots.txt`), {}, ctx);
    assert.equal(await result.text(), policy);
  }
});
