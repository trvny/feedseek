import { mcpResponse } from "./mcp.js";
import { SITE_ALIAS_HOST } from "./site-alias.js";

const OPENAI_CHALLENGE_PATH = "/.well-known/openai-apps-challenge";

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
    if (hostname === SITE_ALIAS_HOST) return ctx.exports.FeedseekSite.fetch(request);
    if (pathname === "/mcp") return mcpResponse(request);
    if (pathname === OPENAI_CHALLENGE_PATH) return openAiChallengeResponse(request, env);
    return ctx.exports.FeedseekProxy.fetch(request);
  },
};
