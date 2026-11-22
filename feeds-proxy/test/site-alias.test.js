import assert from "node:assert/strict";
import { test } from "node:test";
import { siteAliasResponse } from "../src/site-alias.js";

test("WebSub pilot bypasses response caches and conditional upstream fetches", async () => {
  const request = new Request("https://rss.bartek.lol/jbzd.xml", {
    headers: { "if-none-match": '"stale"', accept: "application/atom+xml" },
  });
  const response = await siteAliasResponse(request, async (target, init) => {
    assert.equal(target.href, "https://trvny.github.io/feedseek/jbzd.xml");
    assert.deepEqual(Object.fromEntries(init.headers), { accept: "application/atom+xml" });
    assert.equal(init.cf?.cacheTtl, 0);
    return new Response("<feed/>", { headers: {
      "cache-control": "max-age=600", etag: '"stale"', "last-modified": "Fri, 20 Nov 2026 00:00:00 GMT"
    } });
  });
  assert.equal(response.headers.get("cache-control"), "no-store");
  assert.equal(response.headers.get("etag"), null);
  assert.equal(response.headers.get("last-modified"), null);
  assert.equal(await response.text(), "<feed/>");
});

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

test("preserves Pages canonicals and crawl directives", async () => {
  const canonical = '<link rel="canonical" href="https://trvny.github.io/feedseek/">';
  const page = await siteAliasResponse(new Request("https://rss.bartek.lol/"), async () => new Response(canonical));
  assert.equal(page.headers.get("x-robots-tag"), null);
  assert.equal(await page.text(), canonical);

  const robots = await siteAliasResponse(new Request("https://rss.bartek.lol/robots.txt"), async () =>
    new Response("User-agent: *\nAllow: /\n"));
  assert.equal(robots.headers.get("x-robots-tag"), null);
  assert.equal(await robots.text(), "User-agent: *\nAllow: /\n");

  const feed = await siteAliasResponse(new Request("https://rss.bartek.lol/example.json"), async () =>
    Response.json({}, { headers: { "x-robots-tag": "index" } }));
  assert.equal(feed.headers.get("x-robots-tag"), "index");
});

test("passes through advertised sitemaps without adding noindex", async () => {
  for (const name of ["sitemap.xml", "sitemap-atom.xml", "sitemap-rss.xml"]) {
    const request = new Request(`https://rss.bartek.lol/${name}`, {
      headers: {
        accept: "application/xml",
        "if-none-match": '"cached"',
        "if-modified-since": "Fri, 20 Nov 2026 00:00:00 GMT",
      },
    });
    const response = await siteAliasResponse(request, async (target, init) => {
      assert.equal(target.href, `https://trvny.github.io/feedseek/${name}`);
      assert.deepEqual(Object.fromEntries(init.headers), { accept: "application/xml" });
      return new Response("published sitemap", {
        headers: {
          etag: '"cached"',
          "last-modified": "Fri, 20 Nov 2026 00:00:00 GMT",
          "accept-ranges": "bytes",
        },
      });
    });
    assert.equal(response.status, 200);
    assert.equal(response.headers.get("x-robots-tag"), null, name);
    assert.equal(response.headers.get("etag"), null, name);
    assert.equal(response.headers.get("last-modified"), null, name);
    assert.equal(response.headers.get("accept-ranges"), null, name);
    assert.equal(await response.text(), "published sitemap");
  }
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
  const guide = await siteAliasResponse(new Request("https://rss.bartek.lol/llms-full.txt"), async (_target, init) => {
    assert.deepEqual(Object.fromEntries(init.headers), {});
    return new Response("See https://trvny.github.io/feedseek/jbzd.json", {
      headers: { etag: '"obsolete"', "content-length": "60" },
    });
  });
  assert.equal(guide.headers.get("etag"), null);
  assert.equal(guide.headers.get("content-length"), null);
  assert.equal(await guide.text(), "See https://rss.bartek.lol/jbzd.json");
  const readerGuide = await siteAliasResponse(new Request("https://rss.bartek.lol/reader/index.md"), async () =>
    new Response("[Home](https://trvny.github.io/feedseek/)"));
  assert.equal(await readerGuide.text(), "[Home](https://rss.bartek.lol/)");
  const unavailable = await siteAliasResponse(request, async () => new Response("missing", { status: 404 }));
  assert.equal(unavailable.status, 404);
  assert.equal(await unavailable.text(), "missing");
});

test("publishes agent discovery metadata with precise content types and no noindex", async () => {
  const types = {
    "/.well-known/ard.json": "application/ard+json",
    "/.well-known/ai-catalog.json": "application/ai-catalog+json",
    "/.well-known/mcp/server-card.json": "application/mcp-server-card+json",
  };
  for (const [path, expected] of Object.entries(types)) {
    const response = await siteAliasResponse(new Request("https://rss.bartek.lol" + path), async (target, init) => {
      assert.equal(target.href, "https://trvny.github.io/feedseek" + path);
      assert.deepEqual(Object.fromEntries(init.headers), {});
      return Response.json({ name: "Feedseek" });
    });
    assert.equal(response.status, 200, path);
    assert.equal(response.headers.get("content-type"), expected + "; charset=utf-8", path);
    assert.equal(response.headers.get("access-control-allow-origin"), "*", path);
    assert.equal(response.headers.get("x-robots-tag"), null, path);
    assert.deepEqual(await response.json(), { name: "Feedseek" });
  }
  const response = await siteAliasResponse(new Request("https://rss.bartek.lol/.well-known/unknown.json"), async () => Response.json({}));
  assert.equal(response.headers.get("x-robots-tag"), "noindex, follow");
});
