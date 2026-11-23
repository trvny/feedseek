import { listFeeds, listFeedItems, parseWhen, recentEntries } from "./mcp.js";

const BASE = "https://rss.bartek.lol";
const CORS = {
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS",
  "access-control-allow-headers": "accept, content-type",
};
const JSON_HEADERS = {
  ...CORS,
  "content-type": "application/json; charset=utf-8",
  "x-content-type-options": "nosniff",
  "x-robots-tag": "noindex, follow",
};

class BadRequest extends Error {}

/** @param {Request} request @param {unknown} value @param {number} status */
function response(request, value, status = 200) {
  return new Response(request.method === "HEAD" ? null : JSON.stringify(value), {
    status,
    headers: {
      ...JSON_HEADERS,
      "cache-control": status === 200 ? "public, max-age=60, stale-while-revalidate=300" : "no-store",
      ...(status === 405 ? { allow: "GET, HEAD, OPTIONS" } : {}),
    },
  });
}

/** @param {URLSearchParams} params @param {string[]} allowed */
function validateParams(params, allowed) {
  const names = new Set(allowed);
  for (const key of params.keys()) {
    if (!names.has(key)) throw new BadRequest("Unknown parameter: " + key);
    if (params.getAll(key).length > 1) throw new BadRequest("Repeated parameter: " + key);
  }
}

/** @param {URLSearchParams} params @param {string} key @param {number} fallback @param {number} max */
function integerParam(params, key, fallback, max) {
  const raw = params.get(key);
  if (raw === null) return fallback;
  if (!/^(0|[1-9]\d*)$/.test(raw)) throw new BadRequest("Invalid " + key);
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value > max || (key === "limit" && value < 1)) {
    throw new BadRequest("Invalid " + key);
  }
  return value;
}

/** @param {URLSearchParams} params */
function queryParam(params) {
  const query = params.get("query") || "";
  if (query.length > 500) throw new BadRequest("query exceeds 500 characters");
  return query;
}

/** @param {URLSearchParams} params */
function sourcesParam(params) {
  const raw = params.get("sources");
  if (!raw) return [];
  const sources = raw.split(",").map((part) => part.trim());
  if (sources.length > 20 || sources.some((key) => !/^[a-z0-9_-]{1,64}$/.test(key))) {
    throw new BadRequest("sources must contain 1–20 feed keys");
  }
  return sources;
}

/** Public bounded REST facade over the same source data as MCP. @param {Request} request */
export async function httpApiResponse(request) {
  if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });
  if (request.method !== "GET" && request.method !== "HEAD") {
    return response(request, { error: "Method not allowed" }, 405);
  }
  const url = new URL(request.url);
  const { pathname, searchParams } = url;
  try {
    if (pathname === "/api/v1") {
      validateParams(searchParams, []);
      return response(request, {
        name: "Feedseek", version: "1",
        openapi: BASE + "/openapi.json",
        catalog: BASE + "/model-feeds.json",
        health: BASE + "/health",
        routes: ["/api/v1/feeds", "/api/v1/recent", "/api/v1/feeds/{key}/items"],
      });
    }
    if (pathname === "/api/v1/feeds") {
      validateParams(searchParams, ["query", "limit", "offset"]);
      const result = await listFeeds({
        query: queryParam(searchParams),
        limit: integerParam(searchParams, "limit", 20, 50),
        offset: integerParam(searchParams, "offset", 0, 1000000),
      });
      return response(request, result);
    }
    if (pathname === "/api/v1/recent") {
      validateParams(searchParams, ["query", "limit", "since", "sources"]);
      // RFC 3339 permits lowercase t/z; normalize before shared strict parsing.
      const since = searchParams.get("since")?.replace("t", "T").replace(/z$/, "Z") ?? null;
      if (since !== null && parseWhen(since) === null) {
        throw new BadRequest("since must be a valid RFC 3339 date-time");
      }
      const result = await recentEntries({
        query: queryParam(searchParams),
        since: since || undefined,
        sources: sourcesParam(searchParams),
        limit: integerParam(searchParams, "limit", 20, 100),
      });
      return response(request, result);
    }
    const itemMatch = /^\/api\/v1\/feeds\/([a-z0-9_-]{1,64})\/items$/.exec(pathname);
    if (itemMatch) {
      validateParams(searchParams, ["limit", "offset", "snapshot"]);
      const offset = integerParam(searchParams, "offset", 0, 1000000);
      const snapshot = searchParams.get("snapshot");
      if (offset > 0 && !snapshot) throw new BadRequest("snapshot required when offset > 0");
      if (snapshot && !/^[0-9a-f]{64}$/.test(snapshot)) throw new BadRequest("Invalid snapshot");
      const result = await listFeedItems({
        key: itemMatch[1],
        limit: integerParam(searchParams, "limit", 20, 50),
        offset,
        snapshot,
      });
      return result === null
        ? response(request, { error: "Unknown Feedseek source key" }, 404)
        : response(request, result);
    }
    return response(request, { error: "Unknown API route" }, 404);
  } catch (error) {
    if (error instanceof BadRequest) return response(request, { error: error.message }, 400);
    if (error?.code === "STALE_SNAPSHOT") return response(request, { error: error.message }, 409);
    console.warn("Feedseek HTTP API unavailable", error instanceof Error ? error.message : "unknown error");
    return response(request, { error: "Feedseek upstream temporarily unavailable" }, 503);
  }
}
