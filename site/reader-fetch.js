(() => {
  const nativeFetch = window.fetch.bind(window);
  const FAVICON_PROXY_ORIGIN = "https://feeds-proxy.travny.workers.dev/favicon";

  function faviconCandidates(iconUrl, siteUrl, size = 32) {
    const httpUrl = value => {
      try {
        const url = new URL(String(value || ""));
        return url.protocol === "http:" || url.protocol === "https:" ? url : null;
      } catch {
        return null;
      }
    };

    const icon = httpUrl(iconUrl);
    const site = httpUrl(siteUrl);
    const isManagedResolver = icon?.pathname === "/favicon"
      && ["feeds-proxy.travny.workers.dev", "feeds.trfny.com"].includes(icon.hostname);
    const domain = (isManagedResolver ? icon.searchParams.get("domain") : null)
      || site?.hostname || icon?.hostname || "";
    if (!domain) return icon ? [icon.href] : [];

    const managed = new URL(FAVICON_PROXY_ORIGIN);
    if (isManagedResolver) {
      // Keep source-provided assets and provider preferences during migration.
      for (const key of ["url", "provider"]) {
        const value = icon.searchParams.get(key);
        if (value) managed.searchParams.set(key, value);
      }
    }
    managed.searchParams.set("domain", domain);
    managed.searchParams.set("sz", String(size));

    const rootGuess = site ? new URL("/favicon.ico", site).href : "";
    const isOldResolver = icon && (
      icon.hostname === "www.google.com"
      || icon.hostname === "icons.duckduckgo.com"
    );
    const preferredExplicit = icon
      && icon.href !== rootGuess
      && !isOldResolver
      && !isManagedResolver;

    const candidates = [];
    if (preferredExplicit) candidates.push(icon.href);
    candidates.push(managed.href);
    if (icon) candidates.push(icon.href);
    return [...new Set(candidates)];
  }

  async function allSettledLimited(items, limit, task) {
    const results = new Array(items.length);
    let next = 0;
    const concurrency = Math.min(items.length, Math.max(1, Math.floor(limit) || 1));

    async function worker() {
      while (true) {
        const index = next++;
        if (index >= items.length) return;
        try {
          results[index] = { status: "fulfilled", value: await task(items[index], index) };
        } catch (reason) {
          results[index] = { status: "rejected", reason };
        }
      }
    }

    await Promise.all(Array.from({ length: concurrency }, () => worker()));
    return results;
  }

  async function readTextLimited(response, maxBytes) {
    if (Number(response.headers.get("content-length")) > maxBytes) {
      await response.body?.cancel();
      throw new Error("feed exceeds byte limit");
    }
    if (!response.body) return "";
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const chunks = [];
    let bytes = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        bytes += value.byteLength;
        if (bytes > maxBytes) throw new Error("feed exceeds byte limit");
        chunks.push(decoder.decode(value, { stream: true }));
      }
      chunks.push(decoder.decode());
      return chunks.join("");
    } finally {
      await reader.cancel();
      reader.releaseLock();
    }
  }

  function migrateLegacyFeedMetadata(items, feeds) {
    const feedsByUrl = new Map(feeds.map(feed => [feed.xmlUrl, feed]));
    const feedsByTitle = new Map();
    for (const feed of feeds) {
      if (!feedsByTitle.has(feed.title)) feedsByTitle.set(feed.title, feed);
      else feedsByTitle.set(feed.title, null);
    }
    return items.map(item => {
      const feed = (item.feedUrl && feedsByUrl.get(item.feedUrl))
        || feedsByTitle.get(item.source);
      if (!feed) return item;
      return {
        ...item,
        feedUrl: item.feedUrl || feed.xmlUrl,
        feedSite: item.feedSite || feed.htmlUrl || "",
      };
    });
  }

  function mergeRefreshResults(feeds, results, previousItems) {
    const items = [];
    const failed = [];
    const failedSubscriptions = new Set();
    const feedsByUrl = new Map();
    for (const feed of feeds) {
      if (!feedsByUrl.has(feed.xmlUrl)) feedsByUrl.set(feed.xmlUrl, []);
      feedsByUrl.get(feed.xmlUrl).push(feed);
    }
    const cachedItems = migrateLegacyFeedMetadata(previousItems, feeds);

    results.forEach((result, index) => {
      const feed = feeds[index];
      if (result.status === "fulfilled") items.push(...result.value);
      else {
        failed.push(feed.title);
        failedSubscriptions.add(JSON.stringify([feed.xmlUrl, feed.title]));
      }
    });

    for (const item of cachedItems) {
      const subscriptions = feedsByUrl.get(item.feedUrl) || [];
      const subscription = subscriptions.find(feed => feed.title === item.source)
        || (subscriptions.length === 1 ? subscriptions[0] : null);
      if (!subscription || !failedSubscriptions.has(JSON.stringify([subscription.xmlUrl, subscription.title]))) continue;
      items.push({ ...item, source: subscription.title });
    }

    return { items, failed };
  }


  // Only the same-origin published catalog opts a feed into Model Feed reads.
  function modelFeedUrls(catalog, siteBase) {
    const urls = new Map();
    if (catalog?.format !== "feedseek-model-feed-catalog" ||
        catalog.version !== 1 || !Array.isArray(catalog.feeds)) return urls;
    let origin;
    try { origin = new URL(siteBase).origin; }
    catch { return urls; }

    for (const entry of catalog.feeds) {
      if (!entry || typeof entry.feed_url !== "string" ||
          typeof entry.model_feed_url !== "string") continue;
      try {
        const xml = new URL(entry.feed_url);
        const json = new URL(entry.model_feed_url);
        if (xml.origin !== origin || json.origin !== origin ||
            !xml.pathname.endsWith(".xml") || !json.pathname.endsWith(".json") ||
            xml.username || xml.password || json.username || json.password) continue;
        if (!urls.has(xml.href)) urls.set(xml.href, json.href);
      } catch {
        // Ignore malformed catalog rows. Ordinary XML remains available.
      }
    }
    return urls;
  }

  function parseModelFeed(payload, feed, expectedJsonUrl, maxItems = 10000) {
    const doc = JSON.parse(payload);
    if (!doc || doc.format !== "feedseek-model-feed" || doc.version !== 1 ||
        !Array.isArray(doc.items) || !doc.items.length || doc.items.length > maxItems) {
      throw new Error("unsupported Model Feed");
    }

    function httpUrl(value) {
      if (typeof value !== "string" || !value.trim()) return "";
      try {
        const url = new URL(value);
        return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
      } catch { return ""; }
    }

    if (httpUrl(doc.source_feed) !== httpUrl(feed.xmlUrl) ||
        httpUrl(doc.feed_url) !== httpUrl(expectedJsonUrl)) {
      throw new Error("Model Feed source mismatch");
    }

    const feedSite = httpUrl(doc.home_page_url) || httpUrl(feed.htmlUrl);
    const feedIcon = httpUrl(feed.icon);
    const items = [];
    for (const raw of doc.items) {
      if (!raw || typeof raw.id !== "string" || !raw.id.trim() ||
          typeof raw.title !== "string" || typeof raw.text !== "string" ||
          !["content", "summary", "title"].includes(raw.text_kind)) {
        throw new Error("invalid Model Feed entry");
      }
      const url = httpUrl(raw.url) || httpUrl(raw.external_url);
      if (!url) continue; // Valid model-only entries can lack an article URL.
      const title = raw.title.trim() || "(untitled)";
      let desc = raw.text_kind === "title" ? "" : raw.text.replace(/\s+/gu, " ").trim();
      // Reader previews do not need the complete article body retained by the JSON.
      desc = desc.slice(0, 2048);
      if (desc.toLowerCase() === title.toLowerCase()) desc = "";
      let ts = 0;
      for (const value of [raw.date_published, raw.date_modified]) {
        if (typeof value !== "string") continue;
        const parsed = Date.parse(value);
        if (Number.isFinite(parsed)) { ts = parsed; break; }
      }
      const author = Array.isArray(raw.authors)
        ? raw.authors.find(name => typeof name === "string" && name.trim()) || ""
        : "";
      const categories = Array.isArray(raw.tags)
        ? raw.tags.filter(tag => typeof tag === "string" && tag.trim())
        : [];
      items.push({
        id: raw.id, source: feed.title, feedUrl: feed.xmlUrl, feedIcon, feedSite,
        title, desc, url, author, categories, ts, img: httpUrl(raw.image),
      });
    }
    if (!items.length) throw new Error("Model Feed has no linked entries");
    return items;
  }

  window.FeedseekReaderUtils = {
    allSettledLimited,
    modelFeedUrls,
    parseModelFeed,
    faviconCandidates,
    mergeRefreshResults,
    readTextLimited,
  };

  function configuredProxy() {
    try {
      return JSON.parse(localStorage.getItem("fs:cfg") || "{}").proxy || "";
    } catch {
      return "";
    }
  }

  window.fetch = (input, init) => {
    const inputUrl =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : "";
    const proxy = configuredProxy();

    if (proxy && inputUrl.startsWith(proxy)) {
      try {
        const requestUrl = new URL(inputUrl, document.baseURI);
        const target = requestUrl.searchParams.get("url");
        if (target) {
          const directUrl = new URL(target, document.baseURI);
          if (directUrl.origin === location.origin) {
            return nativeFetch(directUrl.href, init);
          }
        }
      } catch {
        // Keep the original request path for malformed custom proxy URLs.
      }
    }

    return nativeFetch(input, init);
  };
})();
