import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const script = await readFile(new URL("../reader-fetch.js", import.meta.url), "utf8");
function utils() {
  const window = { fetch: async () => new Response("") };
  const context = vm.createContext({
    window, URL,
    document: { baseURI: "https://reader.test/reader/" },
    location: { origin: "https://reader.test" },
    localStorage: { getItem: () => null },
  });
  vm.runInContext(script, context);
  return window.FeedseekReaderUtils;
}

const xmlUrl = "https://reader.test/feed_demo.xml";
const jsonUrl = "https://reader.test/feed_demo.json";
const subscription = {
  title: "My Demo", xmlUrl, htmlUrl: "https://fallback.test/",
  icon: "https://fallback.test/icon.png",
};
function document(items = [{
  id: "urn:demo:1", title: "Demo", text: "  Article\n\n summary  ",
  text_kind: "summary", url: "https://example.test/article",
  date_published: "2026-10-15T12:00:00Z", date_modified: "2026-11-01T12:00:00Z",
  image: "https://example.test/image.png", authors: ["Alice"], tags: ["Tech"],
}]) {
  return {
    format: "feedseek-model-feed", version: 1, source_key: "demo",
    title: "Published Demo", source_feed: xmlUrl, feed_url: jsonUrl,
    home_page_url: "https://example.test/", items,
  };
}

test("published same-origin catalog authorizes JSON without guessing URLs", () => {
  const { modelFeedUrls } = utils();
  const catalog = {
    format: "feedseek-model-feed-catalog", version: 1,
    feeds: [
      { feed_url: xmlUrl, model_feed_url: jsonUrl },
      { feed_url: "https://other.test/news.xml", model_feed_url: "https://other.test/news.json" },
      { feed_url: "https://reader.test/other.xml", model_feed_url: "https://other.test/other.json" },
      { feed_url: "https://reader.test/broken", model_feed_url: "https://reader.test/broken.json" },
      { feed_url: "https://reader.test/with-creds.xml", model_feed_url: "https://user@reader.test/with-creds.json" },
    ],
  };
  const found = modelFeedUrls(catalog, "https://reader.test/reader/");
  assert.deepEqual([...found], [[xmlUrl, jsonUrl]]);
  assert.equal(modelFeedUrls({ ...catalog, version: 2 }, "https://reader.test").size, 0);
  assert.equal(modelFeedUrls(null, "https://reader.test").size, 0);
});

test("Model Feed adapter preserves reader identity, timestamps, metadata and safe preview", () => {
  const { parseModelFeed } = utils();
  const [item] = parseModelFeed(JSON.stringify(document()), subscription, jsonUrl);
  assert.equal(item.id, "urn:demo:1");
  assert.equal(item.source, "My Demo");
  assert.equal(item.feedUrl, xmlUrl);
  assert.equal(item.feedSite, "https://example.test/");
  assert.equal(item.feedIcon, subscription.icon);
  assert.equal(item.title, "Demo");
  assert.equal(item.desc, "Article summary");
  assert.equal(item.url, "https://example.test/article");
  assert.equal(item.img, "https://example.test/image.png");
  assert.equal(item.ts, Date.parse("2026-10-15T12:00:00Z"));
  assert.equal(item.author, "Alice");
  assert.deepEqual(Array.from(item.categories), ["Tech"]);
});

test("Model Feed adapter suppresses unsafe links and title-only descriptions", () => {
  const { parseModelFeed } = utils();
  const input = document([
    { id: "one", title: "One", text: "One", text_kind: "title",
      external_url: "https://example.test/one", image: "javascript:alert(1)" },
    { id: "two", title: "Two", text: "<script>hello</script>", text_kind: "summary",
      url: "javascript:alert(1)" },
  ]);
  const result = parseModelFeed(JSON.stringify(input), subscription, jsonUrl);
  assert.equal(result.length, 1);
  assert.equal(result[0].desc, "");
  assert.equal(result[0].img, "");
  assert.equal(result[0].url, "https://example.test/one");
});

test("Model Feed adapter fails closed on wrong origin, schema, or oversized items", () => {
  const { parseModelFeed } = utils();
  const wrongSource = { ...document(), source_feed: "https://other.test/feed.xml" };
  assert.throws(() => parseModelFeed(JSON.stringify(wrongSource), subscription, jsonUrl), /source mismatch/);
  const wrongUrl = { ...document(), feed_url: "https://reader.test/wrong.json" };
  assert.throws(() => parseModelFeed(JSON.stringify(wrongUrl), subscription, jsonUrl), /source mismatch/);
  assert.throws(() => parseModelFeed(JSON.stringify({ ...document(), version: 2 }), subscription, jsonUrl), /unsupported/);
  assert.throws(() => parseModelFeed(JSON.stringify(document([
    { id: "", title: "Invalid", text: "text", text_kind: "content" },
  ])), subscription, jsonUrl), /invalid/);
  assert.throws(() => parseModelFeed(JSON.stringify(document()), subscription, jsonUrl, 0), /unsupported/);
  assert.throws(() => parseModelFeed(JSON.stringify(document([
    { id: "a", title: "Missing URL", text: "text", text_kind: "summary" },
  ])), subscription, jsonUrl), /no linked entries/);
});

test("broken publication timestamps fall back to modification date", () => {
  const { parseModelFeed } = utils();
  const input = document([{ id: "revision", title: "Revision", text: "News", text_kind: "content",
    url: "https://example.test/revision", date_published: "broken",
    date_modified: "2026-11-04T08:00:00Z" }]);
  const [item] = parseModelFeed(JSON.stringify(input), subscription, jsonUrl);
  assert.equal(item.ts, Date.parse("2026-11-04T08:00:00Z"));
});
