(() => {
  const nativeFetch = window.fetch.bind(window);

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

  function mergeRefreshResults(feeds, results, previousItems) {
    const items = [];
    const failed = [];
    const failedUrls = new Set();
    const titlesByUrl = new Map(feeds.map(feed => [feed.xmlUrl, feed.title]));

    results.forEach((result, index) => {
      const feed = feeds[index];
      if (result.status === "fulfilled") items.push(...result.value);
      else {
        failed.push(feed.title);
        failedUrls.add(feed.xmlUrl);
      }
    });

    for (const item of previousItems) {
      if (!failedUrls.has(item.feedUrl)) continue;
      items.push({ ...item, source: titlesByUrl.get(item.feedUrl) || item.source });
    }

    return { items, failed };
  }

  window.FeedseekReaderUtils = { allSettledLimited, mergeRefreshResults };

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
