import { mcpResponse } from "./mcp.js";
import { httpApiResponse } from "./http-api.js";
import { SITE_ALIAS_HOST, WEBSUB_PILOT_PATHS, siteAliasResponse } from "./site-alias.js";

const OPENAI_CHALLENGE_PATH = "/.well-known/openai-apps-challenge";

/**
 * Public liveness: checks the deployed catalog, not the external feed sources.
 * @param {Request} request
 * @param {typeof fetch} [fetchImpl]
 */
export async function healthResponse(request, fetchImpl = fetch) {
  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response(null, { status: 405, headers: { allow: "GET, HEAD" } });
  }
  const target = new Request("https://rss.bartek.lol/model-feeds.json", { method: "HEAD" });
  const upstream = await siteAliasResponse(target, fetchImpl);
  const healthy = upstream.ok;
  const body = JSON.stringify({
    status: healthy ? "ok" : "degraded",
    service: "feedseek",
    checks: { publishedCatalog: healthy ? "ok" : "unavailable" },
  });
  return new Response(request.method === "HEAD" ? null : body, {
    status: healthy ? 200 : 503,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
      "x-content-type-options": "nosniff",
    },
  });
}


/**
 * @param {Request} request
 * @param {{ OPENAI_APPS_CHALLENGE?: string } | undefined} env
 */
function openAiChallengeResponse(request, env) {
  const token = env?.OPENAI_APPS_CHALLENGE?.trim();
  if (!token) return new Response("Not Found", { status: 404 });
  if (request.method !== "GET" && request.method !== "HEAD") {
    return new Response("Method Not Allowed", {
      status: 405,
      headers: { allow: "GET, HEAD" },
    });
  }
  return new Response(request.method === "HEAD" ? null : token, {
    headers: {
      "cache-control": "no-store",
      "content-type": "text/plain; charset=utf-8",
    },
  });
}

export default {
  /**
   * @param {Request} request
   * @param {{ OPENAI_APPS_CHALLENGE?: string } | undefined} env
   * @param {{ exports: { FeedseekSite: Fetcher, FeedseekProxy: Fetcher } }} ctx
   */
  fetch(request, env, ctx) {
    const { hostname, pathname } = new URL(request.url);
    // MCP works on the canonical domain and remains reachable on the legacy Worker.
    if (pathname === "/mcp") return mcpResponse(request);
    if (pathname === "/api/v1" || pathname.startsWith("/api/v1/")) return httpApiResponse(request);
    if (hostname === SITE_ALIAS_HOST && pathname === "/health") return healthResponse(request);
    if (pathname === OPENAI_CHALLENGE_PATH) return openAiChallengeResponse(request, env);
    // WebSub topics must never be served through the cached WorkerEntrypoint.
    if (hostname === SITE_ALIAS_HOST && WEBSUB_PILOT_PATHS.has(pathname)) {
      return siteAliasResponse(request);
    }
    if (hostname === SITE_ALIAS_HOST) return ctx.exports.FeedseekSite.fetch(request);
    return ctx.exports.FeedseekProxy.fetch(request);
  },
};
