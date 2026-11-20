import assert from "node:assert/strict";
import { test } from "node:test";
import { siteAliasResponse } from "../src/site-alias.js";

test("serves published feeds without forwarding credentials or rewriting entries", async () => {
  const request = new Request("https://rss.bartek.lol/example.xml?source=old", {
    headers: { authorization: "private", cookie: "private", "if-none-match": '"abc"' },
  });
  const response = await siteAliasResponse(request, async (target, init) => {
    assert.equal(target.href, "https://trvny.github.io/feedseek/example.xml?source=old");
    assert.equal(init.redirect, "manual");
    assert.deepEqual(Object.fromEntries(init.headers), { "if-none-match": '"abc"' });
    return new Response("<feed><id>stable</id></feed>", {
      headers: { "content-type": "application/atom+xml", "set-cookie": "example=value" },
    });
  });
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("set-cookie"), null);
  assert.equal(response.headers.get("x-robots-tag"), "noindex, follow");
  assert.equal(await response.text(), "<feed><id>stable</id></feed>");
});

test("keeps Pages redirects on the alias and rejects unrelated destinations", async () => {
  const request = new Request("https://rss.bartek.lol/reader?q=1", { method: "HEAD" });
  const response = await siteAliasResponse(request, async () => Response.redirect("https://trvny.github.io/feedseek/reader/?q=1", 301));
  assert.equal(response.status, 301);
  assert.equal(response.headers.get("location"), "https://rss.bartek.lol/reader/?q=1");
  assert.equal(await response.text(), "");
  const outside = await siteAliasResponse(request, async () => Response.redirect("https://trvny.github.io/elsewhere/"));
  assert.equal(outside.status, 502);
  assert.equal(await outside.text(), "");
  const post = await siteAliasResponse(new Request(request.url, { method: "POST" }), async () => {
    assert.fail("POST must not reach GitHub Pages");
  });
  assert.equal(post.status, 405);
});

test("rebases Reader discovery without serving stale range or conditional responses", async () => {
  const request = new Request("https://rss.bartek.lol/subscriptions.opml", {
    headers: { "if-none-match": '"abc"', range: "bytes=0-42" },
  });
  const response = await siteAliasResponse(request, async (_target, init) => {
    assert.deepEqual(Object.fromEntries(init.headers), {});
    return new Response('<outline xmlUrl="https://trvny.github.io/feedseek/example.xml" />', {
      headers: { etag: '"abc"', "content-type": "application/xml" },
    });
  });
  assert.equal(response.headers.get("etag"), null);
  assert.match(await response.text(), /xmlUrl="https:\/\/rss\.bartek\.lol\/example\.xml"/);

  const catalog = await siteAliasResponse(new Request("https://rss.bartek.lol/model-feeds.json"), async () =>
    Response.json({ xml: "https://trvny.github.io/feedseek/example.xml", model: "https://trvny.github.io/feedseek/example.json" }));
  assert.deepEqual(await catalog.json(), {
    xml: "https://rss.bartek.lol/example.xml",
    model: "https://rss.bartek.lol/example.json",
  });
  const unavailable = await siteAliasResponse(request, async () => new Response("missing", { status: 404 }));
  assert.equal(unavailable.status, 404);
  assert.equal(await unavailable.text(), "missing");
});
