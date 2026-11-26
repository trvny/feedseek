const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

const script = readFileSync(join(__dirname, "../canonical-redirect.js"), "utf8");
function redirect(url, keys = []) {
  let result;
  const location = new URL(url);
  location.replace = value => { result = value; };
  runInNewContext(script, { location, URLSearchParams, localStorage: { length: keys.length, key: i => keys[i] } });
  return result;
}

test("legacy Pages HTML redirects without losing query or fragment", () => {
  for (const path of ["/feedseek", "/feedseek/", "/feedseek/index.html"]) {
    assert.equal(redirect("https://trvny.github.io" + path + "?q=1#feed"), "https://rss.bartek.lol/?q=1#feed");
  }
  for (const path of ["/feedseek/reader", "/feedseek/reader/", "/feedseek/reader/index.html"]) {
    assert.equal(redirect("https://trvny.github.io" + path + "?q=1#entry"), "https://rss.bartek.lol/reader/?q=1#entry");
  }
});

test("canonical HTML, feeds, embed and unrelated hosts never redirect", () => {
  for (const url of [
    "https://rss.bartek.lol/", "https://rss.bartek.lol/reader/",
    "https://trvny.github.io/feedseek/jbzd.xml", "https://trvny.github.io/feedseek/model-feeds.json",
    "https://trvny.github.io/feedseek/meme-widget.html", "https://trvny.github.io/elsewhere/",
    "https://example.com/feedseek/", "https://trvny.github.io/feedseek/sitemap.xml",
  ]) assert.equal(redirect(url), undefined, url);
});

test("legacy Reader remains accessible for existing state or explicit recovery", () => {
  const url = "https://trvny.github.io/feedseek/reader/";
  assert.equal(redirect(url + "?legacy=1"), undefined);
  assert.equal(redirect(url, ["fs:customOpml"]), undefined);
  assert.equal(redirect(url, ["fs:sourceFavorites"]), undefined);
  assert.equal(redirect(url, ["snap"]), undefined);
  assert.equal(redirect(url, ["unrelated"]), "https://rss.bartek.lol/reader/");
  assert.equal(redirect("https://trvny.github.io/feedseek/", ["fs:customOpml"]), "https://rss.bartek.lol/");
});
