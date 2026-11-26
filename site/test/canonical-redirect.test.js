const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

const script = readFileSync(join(__dirname, "../canonical-redirect.js"), "utf8");
async function redirect(url, keys = [], databases = []) {
  let result;
  const location = new URL(url);
  location.replace = value => { result = value; };
  await runInNewContext(script, { location, URLSearchParams, localStorage: { length: keys.length, key: i => keys[i] }, indexedDB: { databases: async () => databases } });
  return result;
}

test("legacy Pages HTML redirects without losing query or fragment", async () => {
  for (const path of ["/feedseek", "/feedseek/", "/feedseek/index.html"]) {
    assert.equal(await redirect("https://trvny.github.io" + path + "?q=1#feed"), "https://rss.bartek.lol/?q=1#feed");
  }
  for (const path of ["/feedseek/reader", "/feedseek/reader/", "/feedseek/reader/index.html"]) {
    assert.equal(await redirect("https://trvny.github.io" + path + "?q=1#entry"), "https://rss.bartek.lol/reader/?q=1#entry");
  }
});

test("canonical HTML, feeds, embed and unrelated hosts never redirect", async () => {
  for (const url of [
    "https://rss.bartek.lol/", "https://rss.bartek.lol/reader/",
    "https://trvny.github.io/feedseek/jbzd.xml", "https://trvny.github.io/feedseek/model-feeds.json",
    "https://trvny.github.io/feedseek/meme-widget.html", "https://trvny.github.io/elsewhere/",
    "https://example.com/feedseek/", "https://trvny.github.io/feedseek/sitemap.xml",
  ]) assert.equal(await redirect(url), undefined, url);
});

test("legacy Reader remains accessible for existing state or explicit recovery", async () => {
  const url = "https://trvny.github.io/feedseek/reader/";
  assert.equal(await redirect(url + "?legacy=1"), undefined);
  assert.equal(await redirect(url, ["fs:customOpml"]), undefined);
  assert.equal(await redirect(url, ["fs:sourceFavorites"]), undefined);
  assert.equal(await redirect(url, ["snap"]), undefined);
  assert.equal(await redirect(url, ["unrelated"]), "https://rss.bartek.lol/reader/");
  assert.equal(await redirect("https://trvny.github.io/feedseek/", ["fs:customOpml"]), "https://rss.bartek.lol/");
});

test("retain IndexedDB-only history and show migration notice without recovery loop", async () => {
  const url = "https://trvny.github.io/feedseek/reader/";
  assert.equal(await redirect(url, [], [{ name: "feedseek-reader" }]), undefined);
  assert.equal(await redirect(url, [], [{ name: "another-app" }]), "https://rss.bartek.lol/reader/");
  const notice = { hidden: true }, recovery = { hidden: false };
  const location = new URL(url);
  location.replace = () => assert.fail("existing history must stay accessible");
  const document = {
    readyState: "complete",
    getElementById: id => ({ legacyReaderNotice: notice, legacyReaderRecovery: recovery })[id],
  };
  const result = await runInNewContext(script, {
    location, document, URLSearchParams,
    indexedDB: { databases: async () => [{ name: "feedseek-reader" }] },
  });
  assert.equal(result, false);
  assert.equal(notice.hidden, false);
  assert.equal(recovery.hidden, true);
  assert.equal(await runInNewContext(script, { location, document, URLSearchParams }), false);
});
