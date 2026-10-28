import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import vm from "node:vm";

const reader = await readFile(new URL("../reader.js", import.meta.url), "utf8");
const utils = await readFile(new URL("../reader-fetch.js", import.meta.url), "utf8");

class Element {
  children = [];
  style = {};
  dataset = {};
  textContent = "";
  constructor(tagName) { this.tagName = tagName; }
  get childNodes() { return this.children; }
  appendChild(child) {
    if (child.tagName === "fragment") this.children.push(...child.children);
    else this.children.push(child);
  }
  append(...children) { children.forEach(child => this.appendChild(child)); }
  replaceChildren(...children) { this.children = []; this.append(...children); }
  setAttribute() {}
  removeAttribute() {}
  focus() { this.focused = true; }
  closest(selector) { return selector === `.${this.className}` ? this : null; }
}

async function makeReader(feeds, entries, snapshotQuota = Infinity) {
  const nodes = new Map();
  const storage = new Map([["fs:cfg", JSON.stringify({ favs: false, thumbs: false })]]);
  const listeners = {};
  const document = {
    baseURI: "https://reader.test/reader/",
    querySelector(selector) {
      if (!nodes.has(selector)) nodes.set(selector, new Element("div"));
      return nodes.get(selector);
    },
    querySelectorAll(selector) {
      return selector === "#list .item"
        ? nodes.get("#list").children.filter(n => n.className === "item") : [];
    },
    createElement: tag => new Element(tag),
    createTextNode: text => ({ textContent: text }),
    createDocumentFragment: () => new Element("fragment"),
    addEventListener: (name, handler) => { listeners[name] = handler; },
  };
  const opml = `<opml><body>${feeds.map(f =>
    `<outline title="${f.title}" xmlUrl="${f.xmlUrl}"/>`
  ).join("")}</body></opml>`;
  const window = { fetch: async () => new Response(opml) };
  const context = vm.createContext({
    document, window, URL, Request, TextDecoder, AbortController, setTimeout, clearTimeout, console,
    location: { origin: "https://reader.test" },
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => {
        if (key === "fs:snap" && JSON.parse(value).items.length > snapshotQuota) {
          throw new Error("Quota exceeded");
        }
        storage.set(key, value);
      },
      removeItem: key => storage.delete(key),
    },
  });
  context.fetch = (...args) => window.fetch(...args);
  vm.runInContext(utils, context);
  vm.runInContext(reader, context);
  context.loadFeed = async feed => entries.get(feed.xmlUrl);
  await vm.runInContext("run()", context);
  const articles = () => nodes.get("#list").children.filter(n => n.className === "item");
  const click = element => listeners.click({ target: element });
  const filter = source => {
    const chip = new Element("button");
    chip.className = "chip";
    chip.dataset.source = source;
    click(chip);
  };
  return { context, storage, nodes, articles, click, filter };
}

function fixture(counts) {
  const feeds = [], entries = new Map();
  counts.forEach((count, source) => {
    const feed = { title: `Source ${source}`, xmlUrl: `https://feed.test/${source}.xml` };
    feeds.push(feed);
    entries.set(feed.xmlUrl, Array.from({ length: count }, (_, i) => ({
      id: `entry-${source}-${i}`,
      source: feed.title, feedUrl: feed.xmlUrl, title: `Article ${source}/${i}`,
      url: `https://article.test/${source}/${i}`, ts: source * 10000 + i,
    })));
  });
  return { feeds, entries };
}

test("refresh retains and snapshots all sources before filtering and pagination", async () => {
  const { feeds, entries } = fixture(Array(110).fill(10));
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 1100);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 1100);
  assert.equal(r.articles().length, 250);
  assert.match(r.nodes.get("#count").textContent, /^250 of 1100 items/);

  r.filter("Source 0");
  assert.equal(r.articles().length, 10);
  assert.equal(r.articles()[0].href, "https://article.test/0/9");
  assert.match(r.nodes.get("#count").textContent, /^10 items/);
});

test("shared page URLs keep distinct entry IDs and independent source memberships", async () => {
  const { feeds, entries } = fixture([3, 1]);
  const first = entries.get(feeds[0].xmlUrl);
  first.forEach(item => { item.url = "https://article.test/changelog"; });
  first[2].id = first[0].id;
  const other = entries.get(feeds[1].xmlUrl)[0];
  other.url = first[0].url;
  other.id = first[0].id;
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 3);
  r.filter("Source 0");
  assert.equal(r.articles().length, 2);
  r.filter("Source 1");
  assert.equal(r.articles().length, 1);
});

test("Atom IDs and RSS GUIDs survive parsing when entries reuse a page URL", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  for (const [rootName, idTag] of [["feed", "id"], ["rss", "guid"]]) {
    r.context.DOMParser = class {
      parseFromString() {
        return {
          documentElement: { tagName: rootName, children: [] },
          querySelector: () => null,
          querySelectorAll: () => ["first", "second"].map(id => ({
            children: [
              { tagName: idTag, textContent: id },
              { tagName: "title", textContent: id },
              { tagName: "link", textContent: "https://article.test/changelog", getAttribute: () => null },
            ],
            getElementsByTagName: () => [],
          })),
        };
      }
    };
    const parsed = vm.runInContext('parseFeed("xml", "Feed", "https://feed.test/feed")', r.context);
    assert.deepEqual(Array.from(parsed, item => item.id), ["first", "second"]);
    assert.equal(parsed[0].url, parsed[1].url);
  }
});

test("Show more reaches the complete source and resets on source changes and refresh", async () => {
  const { feeds, entries } = fixture([600, 10]);
  const r = await makeReader(feeds, entries);
  r.filter("Source 0");
  const more = () => r.nodes.get("#list").children.find(n => n.className === "load-more");
  assert.equal(r.articles().length, 250);
  r.click(more());
  assert.equal(r.articles().length, 500);
  assert.equal(r.articles()[250].focused, true);
  r.filter("Source 0");
  assert.equal(r.articles().length, 500);
  assert.equal(more().textContent, "Show 100 more");
  r.click(more());
  assert.equal(r.articles().length, 600);
  assert.equal(more(), undefined);
  assert.equal(r.articles().at(-1).href, "https://article.test/0/0");
  assert.equal(r.articles()[500].focused, true);

  r.filter("All");
  assert.equal(r.articles().length, 250);
  r.click(more());
  await vm.runInContext("run()", r.context);
  assert.equal(r.articles().length, 250);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 610);
});

test("a failed refresh preserves cached source entries beyond the first display page", async () => {
  const { feeds, entries } = fixture([600, 10]);
  const r = await makeReader(feeds, entries);
  r.context.loadFeed = async feed => {
    if (feed.xmlUrl === feeds[0].xmlUrl) throw new Error("offline");
    return entries.get(feed.xmlUrl);
  };
  await vm.runInContext("run()", r.context);
  r.filter("Source 0");
  assert.equal(vm.runInContext("ITEMS.filter(i => i.source === FILTER).length", r.context), 600);
  assert.match(r.nodes.get("#count").textContent, /^250 of 600 items.*1 failed/);
});

test("offline snapshot bounds do not discard loaded source history", async () => {
  const { feeds, entries } = fixture([6000]);
  const r = await makeReader(feeds, entries);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 6000);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 5000);
});

test("quota-limited snapshots retain the largest fitting prefix", async () => {
  const { feeds, entries } = fixture([1100]);
  const r = await makeReader(feeds, entries, 250);
  assert.equal(JSON.parse(r.storage.get("fs:snap")).items.length, 250);
  assert.equal(vm.runInContext("ITEMS.length", r.context), 1100);
});

test("oversized entry lists fail before materializing individual articles", async () => {
  const { feeds, entries } = fixture([1]);
  const r = await makeReader(feeds, entries);
  r.context.DOMParser = class {
    parseFromString() {
      return {
        documentElement: { tagName: "rss", children: [] },
        querySelector: () => null,
        querySelectorAll: () => ({ length: 10001 }),
      };
    }
  };
  assert.throws(
    () => vm.runInContext('parseFeed("xml", "Large", "https://feed.test/large")', r.context),
    /entry limit/,
  );
});
