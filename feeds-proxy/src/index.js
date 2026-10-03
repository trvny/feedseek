const FETCH_TIMEOUT_MS = 8000;
const DOWNLOAD_SOUNDTRACKS_TIMEOUT_MS = 20000;
const THIRTEEN37X_TIMEOUT_MS = 10000;
const DOWNLOAD_SOUNDTRACKS_ORIGIN = "https://download-soundtracks.com";
const DOWNLOAD_SOUNDTRACKS_HOSTS = new Set(["download-soundtracks.com", "www.download-soundtracks.com"]);
const THIRTEEN37X_ORIGINS = ["https://1337x.to", "https://x1337x.cc"];
const THIRTEEN37X_HOSTS = new Set(THIRTEEN37X_ORIGINS.map((origin) => new URL(origin).hostname));
const DEFAULT_USER_AGENT = "feedseek-reader/2.0";
const BROWSER_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";
const DEFAULT_ACCEPT = "application/atom+xml, application/rss+xml, application/xml, text/xml, application/json, text/plain, text/html;q=0.8, */*;q=0.1";
const MAX_REDIRECTS = 3;
const MAX_RESPONSE_BYTES = 2 * 1024 * 1024;
const MAX_FAVICON_BYTES = 512 * 1024;
const FAVICON_ACCEPT = "image/avif, image/webp, image/png, image/svg+xml, image/*, */*;q=0.1";
const BODYLESS_STATUSES = new Set([101, 204, 205, 304]);
const PROXY_ORIGIN = "https://feeds.trfny.com";
const ROBOTS = "User-agent: *\nAllow: /index.md\nAllow: /llms.txt\nAllow: /llms-full.txt\nDisallow: /\n";
const INDEX_MD = `# Feedseek fetch proxy\n\n> Constrained HTTPS fetch helper used by the Feedseek Reader.\n\nThe proxy accepts a public HTTPS target through the \`url\` query parameter. It blocks private-looking hosts, non-HTTPS targets, unsafe redirects and oversized responses.\n\n- [Feedseek](https://trvny.github.io/feedseek/)\n- [Concise LLM guide](${PROXY_ORIGIN}/llms.txt)\n- [Full LLM guide](${PROXY_ORIGIN}/llms-full.txt)\n- [Source](https://github.com/trvny/feedseek/tree/main/feeds-proxy)\n`;
const LLMS = `# Feedseek fetch proxy\n\n> Constrained public HTTPS fetch helper for Feedseek's browser Reader.\n\n## Resources\n\n- [Proxy overview](${PROXY_ORIGIN}/index.md): Markdown description and security boundaries.\n- [Feedseek site](https://trvny.github.io/feedseek/index.md): main feed directory.\n- [Full proxy guide](${PROXY_ORIGIN}/llms-full.txt): complete proxy documentation.\n- [Source](https://github.com/trvny/feedseek/tree/main/feeds-proxy): implementation and tests.\n`;
const LLMS_FULL = `# Feedseek fetch proxy full documentation\n\nSource: ${PROXY_ORIGIN}/\n\nDescription: Complete LLM-oriented guide to the constrained Feedseek Reader fetch proxy.\n\n## Contract\n\nGET requests with a \`url=https://...\` query parameter fetch a public HTTPS resource for the Reader. Responses are size-bounded and redirects are followed only after each target is revalidated.\n\n## Security boundaries\n\nThe proxy rejects non-HTTPS schemes, credentials in URLs, non-standard ports, localhost/private-looking names and direct IP literals. Redirects are capped and revalidated. Responses are capped at 2 MiB. It is not intended as a general open proxy.\n\n## Search indexing\n\nProxied upstream payloads are returned with X-Robots-Tag noindex,nofollow so the proxy cannot become an indexed duplicate of the source feed.\n\n## Related\n\n- [Feedseek](https://trvny.github.io/feedseek/index.md)\n- [Source](https://github.com/trvny/feedseek/tree/main/feeds-proxy)\n`;


const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "accept, content-type",
};

const SECURITY_HEADERS = {
  "x-content-type-options": "nosniff",
  "content-security-policy": "default-src 'none'; base-uri 'none'; frame-ancestors 'none'",
  "referrer-policy": "no-referrer",
};

/**
 * @param {string} message
 * @param {number} status
 */
function text(message, status) {
  return new Response(message, {
    status,
    headers: {
      ...CORS_HEADERS,
      ...SECURITY_HEADERS,
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

/** @param {string} hostname */
function isBlockedHostname(hostname) {
  const host = hostname.toLowerCase().replace(/\.$/, "");
  if (!host || host === "localhost" || host.endsWith(".localhost")) return true;
  if (host.endsWith(".local") || host.endsWith(".internal") || host.endsWith(".home") || host.endsWith(".lan")) return true;
  if (host.includes(":")) return true;
  if (/^\d{1,3}(?:\.\d{1,3}){3}$/.test(host)) return true;
  return false;
}

/**
 * @param {string} value
 * @param {string | URL | undefined} [base]
 */
function parseTarget(value, base) {
  let target = null;
  try {
    target = new URL(value, base);
  } catch {
    throw new Error("bad url");
  }

  if (target.protocol !== "https:" || target.username || target.password) throw new Error("bad url");
  if (target.port && target.port !== "443") throw new Error("bad url");
  if (isBlockedHostname(target.hostname)) throw new Error("blocked host");
  return target;
}

/**
 * @param {URL} initialUrl
 * @param {{timeoutMs?: number, userAgent?: string, allowedHosts?: Set<string>, accept?: string}} [options]
 */
async function fetchWithRedirects(initialUrl, options = {}) {
  const {
    timeoutMs = FETCH_TIMEOUT_MS,
    userAgent = DEFAULT_USER_AGENT,
    allowedHosts = null,
    accept = DEFAULT_ACCEPT,
  } = options;
  let target = initialUrl;
  const signal = AbortSignal.timeout(timeoutMs);

  for (let redirects = 0; redirects <= MAX_REDIRECTS; redirects++) {
    const response = await fetch(target, {
      headers: {
        "user-agent": userAgent,
        accept,
      },
      redirect: "manual",
      signal,
    });

    if (![301, 302, 303, 307, 308].includes(response.status)) return response;
    if (redirects === MAX_REDIRECTS) throw new Error("too many redirects");

    const location = response.headers.get("location");
    if (!location) throw new Error("bad redirect");
    target = parseTarget(location, target);
    if (allowedHosts && !allowedHosts.has(target.hostname.toLowerCase())) {
      throw new Error("bad redirect");
    }
  }

  throw new Error("too many redirects");
}

/**
 * @param {Response} response
 * @param {number} [maxBytes]
 */
async function readLimited(response, maxBytes = MAX_RESPONSE_BYTES) {
  if (BODYLESS_STATUSES.has(response.status) || !response.body) return null;

  const declared = Number(response.headers.get("content-length") || 0);
  if (declared > maxBytes) throw new Error("response too large");

  const reader = response.body.getReader();
  /** @type {Uint8Array[]} */
  const chunks = [];
  let size = 0;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      size += value.byteLength;
      if (size > maxBytes) {
        await reader.cancel("response too large");
        throw new Error("response too large");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }

  const body = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    body.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return body;
}

/** @type {Record<string, {body: string, contentType: string, maxAge: number}>} */
const DISCOVERY = {
  "/robots.txt": { body: ROBOTS, contentType: "text/plain; charset=utf-8", maxAge: 86400 },
  "/index.md": { body: INDEX_MD, contentType: "text/markdown; charset=utf-8", maxAge: 3600 },
  "/llms.txt": { body: LLMS, contentType: "text/plain; charset=utf-8", maxAge: 3600 },
  "/llms-full.txt": { body: LLMS_FULL, contentType: "text/plain; charset=utf-8", maxAge: 3600 },
};

/** @param {Request} request @param {URL} requestUrl */
function discoveryResponse(request, requestUrl) {
  const discovery = DISCOVERY[requestUrl.pathname];
  if (!discovery || (request.method !== "GET" && request.method !== "HEAD")) return null;
  const { body, contentType, maxAge } = discovery;
  return new Response(request.method === "HEAD" ? null : body, {
    headers: {
      ...CORS_HEADERS,
      ...SECURITY_HEADERS,
      "content-type": contentType,
      "cache-control": `public, max-age=${maxAge}`,
    },
  });
}

/** @param {URL} requestUrl */
function downloadSoundtracksTarget(requestUrl) {
  const path = requestUrl.searchParams.get("path") || "/";
  if (!path.startsWith("/") || path.startsWith("//")) throw new Error("bad path");
  const target = new URL(path, DOWNLOAD_SOUNDTRACKS_ORIGIN);
  if (target.origin !== DOWNLOAD_SOUNDTRACKS_ORIGIN) throw new Error("bad path");
  return target;
}

/** @param {URL} requestUrl */
async function downloadSoundtracksResponse(requestUrl) {
  let target = null;
  try {
    target = downloadSoundtracksTarget(requestUrl);
  } catch {
    return text("bad path", 400);
  }

  let upstream = null;
  try {
    upstream = await fetchWithRedirects(target, {
      timeoutMs: DOWNLOAD_SOUNDTRACKS_TIMEOUT_MS,
      userAgent: BROWSER_USER_AGENT,
      allowedHosts: DOWNLOAD_SOUNDTRACKS_HOSTS,
    });
  } catch (error) {
    const message = error instanceof Error && error.name === "TimeoutError"
      ? "upstream timeout"
      : error instanceof Error
        ? error.message
        : "fetch failed";
    return text(message, 502);
  }

  let body = null;
  try {
    body = await readLimited(upstream);
  } catch (error) {
    return text(error instanceof Error ? error.message : "fetch failed", 502);
  }

  const headers = new Headers({ ...CORS_HEADERS, ...SECURITY_HEADERS });
  headers.set("content-type", upstream.headers.get("content-type") || "text/html; charset=utf-8");
  headers.set("cache-control", upstream.ok ? "public, max-age=300" : "no-store");
  headers.set("x-robots-tag", "noindex, nofollow");
  return new Response(body, { status: upstream.status, headers });
}

async function thirteen37xResponse() {
  let lastUpstream = null;
  let lastError = null;

  for (const origin of THIRTEEN37X_ORIGINS) {
    try {
      const upstream = await fetchWithRedirects(new URL("/trending", origin), {
        timeoutMs: THIRTEEN37X_TIMEOUT_MS,
        userAgent: BROWSER_USER_AGENT,
        allowedHosts: THIRTEEN37X_HOSTS,
      });
      if (upstream.ok) {
        const body = await readLimited(upstream);
        const headers = new Headers({ ...CORS_HEADERS, ...SECURITY_HEADERS });
        headers.set("content-type", upstream.headers.get("content-type") || "text/html; charset=utf-8");
        headers.set("cache-control", "public, max-age=300");
        headers.set("x-robots-tag", "noindex, nofollow");
        return new Response(body, { status: upstream.status, headers });
      }
      lastUpstream = upstream;
    } catch (error) {
      lastError = error;
    }
  }

  if (lastUpstream) {
    let body = null;
    try {
      body = await readLimited(lastUpstream);
    } catch (error) {
      return text(error instanceof Error ? error.message : "fetch failed", 502);
    }
    const headers = new Headers({ ...CORS_HEADERS, ...SECURITY_HEADERS });
    headers.set("content-type", lastUpstream.headers.get("content-type") || "text/html; charset=utf-8");
    headers.set("cache-control", "no-store");
    headers.set("x-robots-tag", "noindex, nofollow");
    return new Response(body, { status: lastUpstream.status, headers });
  }

  const message = lastError instanceof Error && lastError.name === "TimeoutError"
    ? "upstream timeout"
    : lastError instanceof Error
      ? lastError.message
      : "fetch failed";
  return text(message, 502);
}

/** @param {string} value */
function parseFaviconDomain(value) {
  const raw = value.trim().toLowerCase().replace(/\.$/, "");
  if (!raw || raw.includes("/") || raw.includes("@") || raw.includes(":")) {
    throw new Error("bad domain");
  }
  const target = parseTarget(`https://${raw}/`);
  return target.hostname.toLowerCase();
}

/** @param {Uint8Array | null} body @param {string} contentType */
function looksLikeImage(body, contentType) {
  if (!body || body.byteLength < 4) return false;
  if (contentType.startsWith("image/")) return true;

  const head = body.slice(0, 16);
  const ascii = new TextDecoder().decode(body.slice(0, 256)).trimStart().toLowerCase();
  if (head[0] === 0x89 && head[1] === 0x50 && head[2] === 0x4e && head[3] === 0x47) return true;
  if (head[0] === 0xff && head[1] === 0xd8 && head[2] === 0xff) return true;
  if (head[0] === 0x47 && head[1] === 0x49 && head[2] === 0x46 && head[3] === 0x38) return true;
  if (head[0] === 0x00 && head[1] === 0x00 && head[2] === 0x01 && head[3] === 0x00) return true;
  if (ascii.startsWith("<svg") || (ascii.startsWith("<?xml") && ascii.includes("<svg"))) return true;
  return head[0] === 0x52 && head[1] === 0x49 && head[2] === 0x46 && head[3] === 0x46;
}

/** @param {URL} requestUrl @param {string} method */
async function faviconResponse(requestUrl, method = "GET") {
  const rawUrl = requestUrl.searchParams.get("url")?.trim() || "";
  let explicit = null;
  if (rawUrl) {
    try {
      explicit = parseTarget(rawUrl);
    } catch (error) {
      const blocked = error instanceof Error && error.message === "blocked host";
      return text(blocked ? "blocked host" : "bad url", blocked ? 403 : 400);
    }
  }

  let domain = "";
  const rawDomain = requestUrl.searchParams.get("domain")?.trim() || "";
  if (rawDomain) {
    try {
      domain = parseFaviconDomain(rawDomain);
    } catch (error) {
      const blocked = error instanceof Error && error.message === "blocked host";
      return text(blocked ? "blocked host" : "bad domain", blocked ? 403 : 400);
    }
  } else if (explicit) {
    domain = explicit.hostname.toLowerCase();
  }
  if (!domain) return text("bad domain", 400);

  const requestedSize = Number.parseInt(requestUrl.searchParams.get("sz") || "64", 10);
  const size = Number.isFinite(requestedSize)
    ? Math.min(512, Math.max(16, requestedSize))
    : 64;
  const provider = requestUrl.searchParams.get("provider") === "duckduckgo"
    ? "duckduckgo"
    : "google";
  const google = new URL("https://www.google.com/s2/favicons");
  google.searchParams.set("domain", domain);
  google.searchParams.set("sz", String(size));
  const duckduckgo = new URL(`https://icons.duckduckgo.com/ip3/${domain}.ico`);
  const direct = new URL(`https://${domain}/favicon.ico`);
  const resolverOrder = provider === "duckduckgo"
    ? [duckduckgo, google]
    : [google, duckduckgo];
  const candidates = [...resolverOrder, direct];
  if (explicit) candidates.unshift(explicit);
  const seen = new Set();

  for (const target of candidates) {
    if (seen.has(target.href)) continue;
    seen.add(target.href);
    try {
      const upstream = await fetchWithRedirects(target, {
        userAgent: BROWSER_USER_AGENT,
        accept: FAVICON_ACCEPT,
      });
      if (!upstream.ok) continue;
      const body = await readLimited(upstream, MAX_FAVICON_BYTES);
      const contentType = (upstream.headers.get("content-type") || "").split(";")[0].toLowerCase();
      if (!looksLikeImage(body, contentType)) continue;

      const headers = new Headers({ ...CORS_HEADERS, ...SECURITY_HEADERS });
      headers.set("content-type", contentType.startsWith("image/") ? contentType : "image/x-icon");
      headers.set("cache-control", "public, max-age=86400, stale-while-revalidate=604800");
      headers.set("x-robots-tag", "noindex, nofollow");
      return new Response(method === "HEAD" ? null : body, { status: 200, headers });
    } catch {
      // Try the next resolver. One broken favicon must not make the endpoint brittle.
    }
  }

  return text("favicon unavailable", 404);
}


/** @param {URL} requestUrl */
async function proxyResponse(requestUrl) {
  const raw = requestUrl.searchParams.get("url");
  if (!raw) return text("bad url", 400);

  let target = null;
  try {
    target = parseTarget(raw);
  } catch (error) {
    const blocked = error instanceof Error && error.message === "blocked host";
    return text(blocked ? "blocked host" : "bad url", blocked ? 403 : 400);
  }

  let upstream = null;
  try {
    upstream = await fetchWithRedirects(target);
  } catch (error) {
    const message = error instanceof Error && error.name === "TimeoutError"
      ? "upstream timeout"
      : error instanceof Error
        ? error.message
        : "fetch failed";
    return text(message, 502);
  }

  let body = null;
  try {
    body = await readLimited(upstream);
  } catch (error) {
    return text(error instanceof Error ? error.message : "fetch failed", 502);
  }

  const headers = new Headers({ ...CORS_HEADERS, ...SECURITY_HEADERS });
  headers.set("content-type", upstream.headers.get("content-type") || "application/xml; charset=utf-8");
  headers.set("cache-control", upstream.ok ? "public, max-age=900" : "no-store");
  headers.set("x-robots-tag", "noindex, nofollow");
  return new Response(body, { status: upstream.status, headers });
}

export default {
  /** @param {Request} request */
  fetch(request) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS_HEADERS });
    const requestUrl = new URL(request.url);
    const discovery = discoveryResponse(request, requestUrl);
    if (discovery) return discovery;
    if (requestUrl.pathname === "/favicon") {
      if (request.method !== "GET" && request.method !== "HEAD") {
        return text("method not allowed", 405);
      }
      return faviconResponse(requestUrl, request.method);
    }
    if (request.method !== "GET") return text("method not allowed", 405);
    if (requestUrl.pathname === "/download-soundtracks") {
      return downloadSoundtracksResponse(requestUrl);
    }
    if (requestUrl.pathname === "/1337x") {
      return thirteen37xResponse();
    }
    return proxyResponse(requestUrl);
  },
};
