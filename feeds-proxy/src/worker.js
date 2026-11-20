import { WorkerEntrypoint } from "cloudflare:workers";
import proxy from "./index.js";
import { siteAliasResponse } from "./site-alias.js";

export { default } from "./app.js";

export class FeedseekSite extends WorkerEntrypoint {
  /** @param {Request} request */
  fetch(request) {
    return siteAliasResponse(request);
  }
}

export class FeedseekProxy extends WorkerEntrypoint {
  /** @param {Request} request */
  fetch(request) {
    return proxy.fetch(request);
  }
}
