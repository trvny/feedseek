(() => {
  const nativeFetch = window.fetch.bind(window);
  const FAVICON_PROXY_ORIGIN = "https://feeds.trfny.com/favicon";

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
    const domain = site?.hostname || icon?.hostname || "";
    if (!domain) return icon ? [icon.href] : [];

    const managed = new URL(FAVICON_PROXY_ORIGIN);
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
      && !(icon.hostname === "feeds.trfny.com" && icon.pathname === "/favicon");

    const candidates = [];
    if (preferredExplicit) candidates.push(icon.href);
    if (icon?.hostname === "feeds.trfny.com" && icon.pathname === "/favicon") {
      candidates.push(icon.href);
    }
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
    const failedUrls = new Set();
    const titlesByUrl = new Map(feeds.map(feed => [feed.xmlUrl, feed.title]));
    const cachedItems = migrateLegacyFeedMetadata(previousItems, feeds);

    results.forEach((result, index) => {
      const feed = feeds[index];
      if (result.status === "fulfilled") items.push(...result.value);
      else {
        failed.push(feed.title);
        failedUrls.add(feed.xmlUrl);
      }
    });

    for (const item of cachedItems) {
      if (!failedUrls.has(item.feedUrl)) continue;
      items.push({ ...item, source: titlesByUrl.get(item.feedUrl) || item.source });
    }

    return { items, failed };
  }

  window.FeedseekReaderUtils = {
    allSettledLimited,
    faviconCandidates,
    mergeRefreshResults,
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
