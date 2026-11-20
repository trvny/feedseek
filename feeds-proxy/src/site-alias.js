export const SITE_ALIAS_HOST = "rss.bartek.lol";
const PAGES = new URL("https://trvny.github.io/feedseek/");
const REQUEST_HEADERS = ["accept", "if-none-match", "if-modified-since", "if-range", "range"];

/** @param {Request} request @param {typeof fetch} fetchImpl */
export async function siteAliasResponse(request, fetchImpl = fetch) {
  const { method } = request;
  if (method !== "GET" && method !== "HEAD") {
    return new Response(null, { status: 405, headers: { allow: "GET, HEAD" } });
  }

  const alias = new URL(request.url);
  const source = new URL(PAGES);
  source.pathname += alias.pathname.slice(1);
  source.search = alias.search;
  const headers = new Headers();
  for (const name of REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value !== null) headers.set(name, value);
  }

  try {
    const upstream = await fetchImpl(source, { method, headers, redirect: "manual", signal: AbortSignal.timeout(12000) });
    const responseHeaders = new Headers(upstream.headers);
    responseHeaders.delete("set-cookie");
    responseHeaders.set("x-robots-tag", "noindex, follow");
    responseHeaders.set("x-content-type-options", "nosniff");
    const location = responseHeaders.get("location");
    if (location && upstream.status >= 300 && upstream.status < 400) {
      const target = new URL(location, source);
      if (target.origin !== PAGES.origin || !target.pathname.startsWith(PAGES.pathname)) {
        throw new Error("Unexpected Pages redirect");
      }
      alias.pathname = "/" + target.pathname.slice(PAGES.pathname.length);
      alias.search = target.search;
      alias.hash = target.hash;
      responseHeaders.set("location", alias.href);
    }
    return new Response(method === "HEAD" ? null : upstream.body, { status: upstream.status, headers: responseHeaders });
  } catch {
    return new Response(method === "HEAD" ? null : "Feedseek temporarily unavailable", {
      status: 502,
      headers: { "cache-control": "no-store", "content-type": "text/plain; charset=utf-8" },
    });
  }
}
