import assert from "node:assert/strict";
import test from "node:test";

import worker from "../src/index.js";

const proxyRequest = (target, init) =>
  new Request(`https://proxy.test/?url=${encodeURIComponent(target)}`, init);

async function withFetch(mockFetch, run) {
  const original = globalThis.fetch;
  globalThis.fetch = mockFetch;
  try {
    return await run();
  } finally {
    globalThis.fetch = original;
  }
}

test("forwards valid HTTPS feeds with cache and security headers", async () => {
  let seenUrl = null;
  let seenInit = null;

  await withFetch(async (url, init) => {
    seenUrl = String(url);
    seenInit = init;
    return new Response("<rss/>", {
      status: 200,
      headers: { "content-type": "application/rss+xml" },
    });
  }, async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/feed.xml"));

    assert.equal(response.status, 200);
    assert.equal(await response.text(), "<rss/>");
    assert.equal(response.headers.get("content-type"), "application/rss+xml");
    assert.equal(response.headers.get("cache-control"), "public, max-age=900");
    assert.equal(response.headers.get("access-control-allow-origin"), "*");
    assert.equal(response.headers.get("x-content-type-options"), "nosniff");
    assert.equal(response.headers.get("x-robots-tag"), "noindex, nofollow");
    assert.equal(seenUrl, "https://example.com/feed.xml");
    assert.equal(seenInit.redirect, "manual");
    assert.equal(seenInit.headers["user-agent"], "feedseek-reader/2.0");
  });
});



test("serves favicons through one stable image endpoint", async () => {
  const seen = [];
  await withFetch((url, init) => {
    seen.push({ url: String(url), init });
    return Promise.resolve(new Response(new Uint8Array([0x89, 0x50, 0x4e, 0x47]), {
      status: 200,
      headers: { "content-type": "image/png" },
    }));
  }, async () => {
    const explicit = encodeURIComponent("https://example.com/assets/icon.png");
    const response = await worker.fetch(new Request(
      `https://proxy.test/favicon?domain=example.com&url=${explicit}&sz=64`,
    ));

    assert.equal(response.status, 200);
    assert.equal(response.headers.get("content-type"), "image/png");
    assert.match(response.headers.get("cache-control"), /max-age=86400/);
    assert.equal(response.headers.get("access-control-allow-origin"), "*");
    assert.equal(response.headers.get("x-content-type-options"), "nosniff");
    assert.equal(seen[0].url, "https://example.com/assets/icon.png");
    assert.equal(seen[0].init.headers.accept.startsWith("image/"), true);
  });
});

test("falls back from a bad explicit favicon to a resolver", async () => {
  const seen = [];
  await withFetch((url) => {
    seen.push(String(url));
    if (seen.length === 1) {
      return Promise.resolve(new Response("<html>not an icon</html>", {
        status: 200,
        headers: { "content-type": "text/html" },
      }));
    }
    return Promise.resolve(new Response(new Uint8Array([0x00, 0x00, 0x01, 0x00]), {
      status: 200,
      headers: { "content-type": "image/x-icon" },
    }));
  }, async () => {
    const explicit = encodeURIComponent("https://example.com/favicon.ico");
    const response = await worker.fetch(new Request(
      `https://proxy.test/favicon?domain=example.com&url=${explicit}&sz=32`,
    ));

    assert.equal(response.status, 200);
    assert.equal(seen[0], "https://example.com/favicon.ico");
    assert.match(seen[1], /^https:\/\/www\.google\.com\/s2\/favicons\?/);
    assert.match(seen[1], /domain=example\.com/);
    assert.match(seen[1], /sz=32/);
  });
});

test("favicon endpoint prefers the requested resolver and supports HEAD", async () => {
  let seen = "";
  await withFetch((url) => {
    seen = String(url);
    return Promise.resolve(new Response(new Uint8Array([0x00, 0x00, 0x01, 0x00]), {
      status: 200,
      headers: { "content-type": "image/x-icon" },
    }));
  }, async () => {
    const response = await worker.fetch(new Request(
      "https://proxy.test/favicon?domain=example.com&provider=duckduckgo&sz=9999",
      { method: "HEAD" },
    ));

    assert.equal(response.status, 200);
    assert.equal(await response.text(), "");
    assert.equal(seen, "https://icons.duckduckgo.com/ip3/example.com.ico");
  });
});

test("favicon endpoint rejects blocked or malformed domains before fetching", async () => {
  let calls = 0;
  await withFetch(() => {
    calls += 1;
    return Promise.resolve(new Response("unexpected"));
  }, async () => {
    const privateHost = await worker.fetch(new Request(
      "https://proxy.test/favicon?domain=127.0.0.1",
    ));
    const malformed = await worker.fetch(new Request(
      "https://proxy.test/favicon?domain=example.com%2Fevil",
    ));

    assert.equal(privateHost.status, 403);
    assert.equal(malformed.status, 400);
    assert.equal(calls, 0);
  });
});

test("uses the allowlisted Download Soundtracks fetch route", async () => {
  let seenUrl;
  let seenInit;

  await withFetch((url, init) => {
    seenUrl = String(url);
    seenInit = init;
    return Promise.resolve(new Response("<html>ok</html>", {
      status: 200,
      headers: { "content-type": "text/html; charset=UTF-8" },
    }));
  }, async () => {
    const response = await worker.fetch(new Request(
      "https://proxy.test/download-soundtracks?path=%2Fpage%2F2%2F",
    ));

    assert.equal(response.status, 200);
    assert.equal(await response.text(), "<html>ok</html>");
    assert.equal(response.headers.get("cache-control"), "public, max-age=300");
    assert.equal(seenUrl, "https://download-soundtracks.com/page/2/");
    assert.match(seenInit.headers["user-agent"], /Chrome\/140/);
    assert.ok(seenInit.signal instanceof AbortSignal);
  });
});

test("uses the host-locked 1337x route with browser headers and mirror fallback", async () => {
  const calls = [];

  await withFetch((url, init) => {
    calls.push({ url: String(url), init });
    if (calls.length === 1) return Promise.resolve(new Response("blocked", { status: 403 }));
    return Promise.resolve(new Response("<html>trending</html>", {
      status: 200,
      headers: { "content-type": "text/html; charset=UTF-8" },
    }));
  }, async () => {
    const response = await worker.fetch(new Request("https://proxy.test/1337x"));

    assert.equal(response.status, 200);
    assert.equal(await response.text(), "<html>trending</html>");
    assert.deepEqual(calls.map((call) => call.url), [
      "https://1337x.to/trending",
      "https://x1337x.cc/trending",
    ]);
    assert.match(calls[0].init.headers["user-agent"], /Chrome\/140/);
    assert.equal(response.headers.get("cache-control"), "public, max-age=300");
  });
});

test("rejects authority changes in the Download Soundtracks path", async () => {
  let calls = 0;
  await withFetch(() => {
    calls += 1;
    return Promise.resolve(new Response("unexpected"));
  }, async () => {
    const response = await worker.fetch(new Request(
      "https://proxy.test/download-soundtracks?path=%2F%2Fevil.example%2F",
    ));
    assert.equal(response.status, 400);
    assert.equal(await response.text(), "bad path");
    assert.equal(calls, 0);
  });
});

test("rejects Download Soundtracks redirects to another host", async () => {
  await withFetch(() => Promise.resolve(new Response(null, {
    status: 302,
    headers: { location: "https://example.com/escape" },
  })), async () => {
    const response = await worker.fetch(new Request(
      "https://proxy.test/download-soundtracks?path=%2F",
    ));
    assert.equal(response.status, 502);
    assert.equal(await response.text(), "bad redirect");
  });
});

test("follows relative redirects and revalidates the target", async () => {
  const calls = [];

  await withFetch(async (url) => {
    calls.push(String(url));
    if (calls.length === 1) {
      return new Response(null, { status: 302, headers: { location: "/final.xml" } });
    }
    return new Response("done", { status: 200 });
  }, async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/start"));

    assert.equal(response.status, 200);
    assert.equal(await response.text(), "done");
    assert.deepEqual(calls, [
      "https://example.com/start",
      "https://example.com/final.xml",
    ]);
  });
});

test("rejects non-HTTPS and private-looking targets before fetching", async () => {
  let calls = 0;

  await withFetch(async () => {
    calls += 1;
    return new Response("unexpected");
  }, async () => {
    const http = await worker.fetch(proxyRequest("http://example.com/feed"));
    const privateHost = await worker.fetch(proxyRequest("https://127.0.0.1/feed"));

    assert.equal(http.status, 400);
    assert.equal(await http.text(), "bad url");
    assert.equal(privateHost.status, 403);
    assert.equal(await privateHost.text(), "blocked host");
    assert.equal(calls, 0);
  });
});

test("rejects redirects to blocked hosts", async () => {
  await withFetch(async () =>
    new Response(null, { status: 302, headers: { location: "https://localhost/private" } }),
  async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/start"));

    assert.equal(response.status, 502);
    assert.equal(await response.text(), "blocked host");
    assert.equal(response.headers.get("cache-control"), "no-store");
  });
});

test("rejects responses over the declared size limit", async () => {
  await withFetch(async () =>
    new Response("x", { headers: { "content-length": String(2 * 1024 * 1024 + 1) } }),
  async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/huge"));

    assert.equal(response.status, 502);
    assert.equal(await response.text(), "response too large");
    assert.equal(response.headers.get("cache-control"), "no-store");
  });
});

test("keeps upstream errors uncached", async () => {
  await withFetch(async () => new Response("missing", { status: 404 }), async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/missing"));

    assert.equal(response.status, 404);
    assert.equal(await response.text(), "missing");
    assert.equal(response.headers.get("cache-control"), "no-store");
  });
});

test("maps upstream timeouts to a 502", async () => {
  const timeout = Object.assign(new Error("timed out"), { name: "TimeoutError" });

  await withFetch(async () => {
    throw timeout;
  }, async () => {
    const response = await worker.fetch(proxyRequest("https://example.com/slow"));

    assert.equal(response.status, 502);
    assert.equal(await response.text(), "upstream timeout");
  });
});

test("answers preflight and rejects non-GET methods", async () => {
  const options = await worker.fetch(new Request("https://proxy.test/", { method: "OPTIONS" }));
  const post = await worker.fetch(new Request("https://proxy.test/", { method: "POST" }));

  assert.equal(options.status, 204);
  assert.equal(options.headers.get("access-control-allow-methods"), "GET, HEAD, OPTIONS");
  assert.equal(post.status, 405);
  assert.equal(await post.text(), "method not allowed");
  assert.equal(post.headers.get("cache-control"), "no-store");
});


test("supports HEAD for public discovery documents", async () => {
  const response = await worker.fetch(new Request("https://feeds.trfny.com/llms-full.txt", { method: "HEAD" }));
  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "text/plain; charset=utf-8");
  assert.equal(await response.text(), "");
});

test("serves llms v2 discovery documents without a proxy target", async () => {
  for (const [path, needle] of [
    ["/index.md", "# Feedseek fetch proxy"],
    ["/llms.txt", "/index.md"],
    ["/llms-full.txt", "# Feedseek fetch proxy full documentation"],
    ["/robots.txt", "Disallow: /"],
  ]) {
    const response = await worker.fetch(new Request(`https://feeds.trfny.com${path}`));
    assert.equal(response.status, 200);
    assert.match(await response.text(), new RegExp(needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
});
