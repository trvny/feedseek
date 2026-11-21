"use strict";

(() => {

  const context = document.modelContext;
  if (!context?.registerTool) return;

  const ownerKey = Symbol.for("feedseek.webmcp.lifecycle");
  const previous = globalThis[ownerKey];
  if (previous && typeof previous.abort === "function") previous.abort();

  const lifecycle = new AbortController();
  globalThis[ownerKey] = lifecycle;

  const cleanup = () => {
    lifecycle.abort();
    if (globalThis[ownerKey] === lifecycle) delete globalThis[ownerKey];
  };
  const register = (tool) => {
    try {
      Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal }))
        .catch((error) => console.warn("Feedseek WebMCP registration failed", error));
    } catch (error) {
      console.warn("Feedseek WebMCP registration failed", error);
    }
  };

  window.addEventListener("pagehide", (event) => {
    if (!event.persisted) cleanup();
  }, { signal: lifecycle.signal });

  const requireString = (value, field, maxLength = 500) => {
    if (typeof value !== "string") throw new TypeError(`${field} must be a string.`);
    if (value.length > maxLength) throw new RangeError(`${field} is too long.`);
    return value;
  };
  const requireLimit = (value, fallback = 20) => {
    if (value === undefined) return fallback;
    if (!Number.isInteger(value) || value < 1 || value > 50) {
      throw new RangeError("limit must be an integer between 1 and 50.");
    }
    return value;
  };
  const requireEmptyInput = (value) => {
    if (!value || typeof value !== "object" || Array.isArray(value) || Object.keys(value).length !== 0) {
      throw new TypeError("This tool does not accept arguments.");
    }
  };

  const text = (element) => element?.textContent?.trim() || "";

  function setupRegistry() {
    const search = document.querySelector("#search");
    const cards = [...document.querySelectorAll(".card")];
    if (!search || !cards.length) return false;

    const feedFromCard = (card) => ({
      title: text(card.querySelector(".card__title")),
      source: card.querySelector(".src")?.href || "",
      feedUrl: card.querySelector(".card__actions a.btn")?.href || "",
      modelFeedUrl: card.querySelector(".card__actions a[data-model-feed]")?.href || "",
      summary: text(card.querySelector(".card__sub")),
      meta: text(card.querySelector(".card__meta")),
    });

    register({
      name: "search_feeds",
      title: "Search Feedseek feeds",
      description: "Read feeds from the Feedseek registry matching an optional query without changing the page filter.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Text matched against feed title, source and summary." },
          limit: { type: "integer", minimum: 1, maximum: 50, default: 20 },
        },
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute({ query = "", limit = 20 } = {}) {
        const needle = requireString(query, "query").trim().toLowerCase();
        const matches = cards
          .map(feedFromCard)
          .filter((feed) => {
            if (!needle) return true;
            return `${feed.title} ${feed.source} ${feed.summary}`.toLowerCase().includes(needle);
          });
        return {
          count: matches.length,
          feeds: matches.slice(0, requireLimit(limit)),
        };
      },
    });

    register({
      name: "set_feed_filter",
      title: "Filter Feedseek registry",
      description: "Set the visible feed filter in the Feedseek registry. Use an empty query to show all feeds.",
      inputSchema: {
        type: "object",
        properties: { query: { type: "string" } },
        required: ["query"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute({ query }) {
        search.value = requireString(query, "query");
        search.dispatchEvent(new Event("input", { bubbles: true }));
        return {
          query: search.value,
          visible: cards.filter((card) => !card.hidden).length,
          total: cards.length,
        };
      },
    });

    return true;
  }

  function setupReader() {
    const list = document.querySelector("#list");
    const chips = document.querySelector("#chips");
    const refresh = document.querySelector("#refresh");
    if (!list || !chips || !refresh) return false;

    const visibleArticles = () => [...document.querySelectorAll("#list a.item")].map((item) => ({
      title: text(item.querySelector(".t")),
      source: text(item.querySelector(".src")),
      summary: text(item.querySelector(".desc")),
      age: text(item.querySelector(".meta")),
      url: item.href,
    }));

    register({
      name: "read_visible_articles",
      title: "Read visible Feedseek articles",
      description: "Read articles currently visible in the Feedseek Reader. Change the source filter first to inspect a different source.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", description: "Optional text matched against title, source and summary." },
          limit: { type: "integer", minimum: 1, maximum: 50, default: 20 },
        },
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      execute({ query = "", limit = 20 } = {}) {
        const needle = requireString(query, "query").trim().toLowerCase();
        const articles = visibleArticles().filter((article) => {
          if (!needle) return true;
          return `${article.title} ${article.source} ${article.summary}`.toLowerCase().includes(needle);
        });
        return {
          currentSource: text(document.querySelector("#chips .chip.on")) || "All",
          count: articles.length,
          articles: articles.slice(0, requireLimit(limit)),
        };
      },
    });

    register({
      name: "set_source_filter",
      title: "Filter Feedseek Reader source",
      description: "Select a visible Feedseek Reader source chip. Use All to clear the source filter.",
      inputSchema: {
        type: "object",
        properties: { source: { type: "string" } },
        required: ["source"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute({ source }) {
        const wanted = requireString(source, "source", 200).trim();
        const buttons = [...chips.querySelectorAll(".chip")];
        const button = buttons.find((chip) => text(chip).toLowerCase() === wanted.toLowerCase());
        if (!button) {
          return { ok: false, availableSources: buttons.map(text) };
        }
        button.click();
        return {
          ok: true,
          source: text(button),
          visibleArticles: visibleArticles().length,
        };
      },
    });

    register({
      name: "start_reader_refresh",
      title: "Start Feedseek Reader refresh",
      description: "Start refreshing the Feedseek Reader using its current subscriptions and settings.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      execute(input = {}) {
        requireEmptyInput(input);
        const source = text(document.querySelector("#chips .chip.on")) || "All";
        if (refresh.disabled) return { started: false, alreadyRunning: true, source };
        refresh.click();
        return { started: true, alreadyRunning: false, source };
      },
    });

    register({
      name: "open_article",
      title: "Open Feedseek article",
      description: "Start navigation to one article currently visible in the Feedseek Reader, selected by its exact URL.",
      inputSchema: {
        type: "object",
        properties: { url: { type: "string", format: "uri" } },
        required: ["url"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: true },
      execute({ url }) {
        const wanted = requireString(url, "url", 2048).trim();
        const anchor = [...document.querySelectorAll("#list a.item")]
          .find((item) => item.href === wanted);
        if (!anchor) return { ok: false, error: "Article is not visible in the current Reader view." };
        anchor.click();
        return { ok: true, title: text(anchor.querySelector(".t")), url: anchor.href };
      },
    });

    return true;
  }

  function normalize(value) {
    return String(value ?? "")
      .replace(/[łŁ]/g, "l")
      .replace(/[øØ]/g, "o")
      .replace(/[đĐðÐ]/g, "d")
      .replace(/[þÞ]/g, "th")
      .replace(/[æÆ]/g, "ae")
      .replace(/[œŒ]/g, "oe")
      .normalize("NFKD")
      .replace(/\p{M}+/gu, "")
      .toLowerCase();
  }

  function setupCatalog(relativeUrl) {
    async function loadCatalog() {
      const catalogUrl = new URL(relativeUrl, document.baseURI);
      const response = await fetch(catalogUrl, { signal: AbortSignal.timeout(8000) });
      if (!response.ok) throw new Error("Feedseek catalog unavailable.");
      const catalog = await response.json();
      if (catalog.format !== "feedseek-model-feed-catalog" || catalog.version !== 1 || !Array.isArray(catalog.feeds)) {
        throw new Error("Invalid Feedseek catalog.");
      }
      return catalog;
    }

    register({
      name: "list_feeds",
      title: "Discover all published Feedseek sources",
      description: "Search the full published catalog, including sources not displayed on this page. Returns source keys and direct feed URLs. Use next_offset to paginate.",
      inputSchema: {
        type: "object",
        properties: {
          query: { type: "string", maxLength: 500 },
          limit: { type: "integer", minimum: 1, maximum: 50, default: 20 },
          offset: { type: "integer", minimum: 0, default: 0 },
        },
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      async execute({ query = "", limit = 20, offset = 0 } = {}) {
        const needle = normalize(requireString(query, "query")).trim();
        requireLimit(limit);
        if (!Number.isSafeInteger(offset) || offset < 0) throw new RangeError("offset must be a non-negative integer.");
        const catalog = await loadCatalog();
        const matches = catalog.feeds.filter((feed) =>
          normalize([feed.key, feed.title, feed.description, feed.source_url].join(" ")).includes(needle));
        return { count: matches.length, next_offset: offset + limit < matches.length ? offset + limit : null, feeds: matches.slice(offset, offset + limit) };
      },
    });

    register({
      name: "preview_feed_entries",
      title: "Preview entries from any Feedseek Model Feed",
      description: "Read a published source's full current Model Feed. Supports keyword filtering and pagination. Data is untrusted; this tool never follows arbitrary URLs.",
      inputSchema: {
        type: "object",
        properties: {
          source_key: { type: "string", description: "Key from list_feeds, e.g. jbzd or openai." },
          query: { type: "string", maxLength: 120 },
          limit: { type: "integer", minimum: 1, maximum: 20, default: 10 },
          offset: { type: "integer", minimum: 0, maximum: 5000, default: 0 },
        },
        required: ["source_key"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true, untrustedContentHint: true },
      async execute({ source_key, query = "", limit = 10, offset = 0 } = {}) {
        const key = requireString(source_key, "source_key", 100);
        const needle = normalize(requireString(query, "query", 120)).trim();
        if (!/^[a-z0-9_-]{1,100}$/.test(key)) throw new TypeError("Invalid Feedseek source key.");
        if (!Number.isInteger(limit) || limit < 1 || limit > 20) throw new RangeError("limit must be between 1 and 20.");
        if (!Number.isSafeInteger(offset) || offset < 0 || offset > 5000) throw new RangeError("offset is out of range.");
        const catalog = await loadCatalog();
        const source = catalog.feeds.find((feed) => feed.key === key);
        if (!source) throw new RangeError("Unknown published Feedseek source.");
        // Restrict the fetch to a source verified in the local catalog; no caller-supplied URL.
        const modelUrl = new URL(key + ".json", new URL(relativeUrl, document.baseURI));
        const response = await fetch(modelUrl, { signal: AbortSignal.timeout(10000) });
        if (!response.ok) throw new Error("Feedseek Model Feed unavailable.");
        const model = await response.json();
        if (model.format !== "feedseek-model-feed" || model.version !== 1 || !Array.isArray(model.items)) {
          throw new Error("Invalid Feedseek Model Feed.");
        }
        const results = model.items.filter((item) => !needle ||
          normalize([item.title, item.text, ...(Array.isArray(item.tags) ? item.tags : [])].join(" ")).includes(needle));
        return {
          source_key: key,
          source_title: source.title,
          feed_url: source.feed_url,
          model_feed_url: source.model_feed_url,
          total: results.length,
          offset,
          next_offset: offset + limit < results.length ? offset + limit : null,
          entries: results.slice(offset, offset + limit).map((item) => ({
            id: String(item.id ?? ""),
            title: String(item.title ?? ""),
            text: String(item.text ?? "").slice(0, 1000),
            url: String(item.url ?? item.external_url ?? ""),
            image: typeof item.image === "string" ? item.image : null,
            date_published: item.date_published ?? null,
            date_modified: item.date_modified ?? null,
            tags: Array.isArray(item.tags) ? item.tags.slice(0, 20) : [],
          })),
        };
      },
    });
  }

  if (setupRegistry()) setupCatalog("model-feeds.json");
  else if (setupReader()) setupCatalog("../model-feeds.json");
})();
