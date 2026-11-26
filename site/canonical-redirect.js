globalThis.FeedseekCanonicalRedirect = (async () => {
  const { location } = globalThis;
  if (location.origin !== "https://trvny.github.io") return;
  const routes = {
    "/feedseek": "/",
    "/feedseek/": "/",
    "/feedseek/index.html": "/",
    "/feedseek/reader": "/reader/",
    "/feedseek/reader/": "/reader/",
    "/feedseek/reader/index.html": "/reader/",
  };
  if (!Object.hasOwn(routes, location.pathname)) return;
  const path = routes[location.pathname];
  const target = "https://rss.bartek.lol" + path + location.search + location.hash;
  if (path === "/reader/") {
    let retain = new URLSearchParams(location.search).get("legacy") === "1";
    try {
      const storage = globalThis.localStorage;
      retain ||= Array.from({ length: storage?.length || 0 }, (_, i) => storage.key(i))
        .some(key => key?.startsWith("fs:") || ["proxy", "opml", "snap"].includes(key));
    } catch {
      // Storage unavailable; explicit recovery URL still works.
    }
    if (!retain) {
      try {
        // Match reader-cache.js; enumerate before Reader startup creates its DB.
        const databases = await globalThis.indexedDB?.databases();
        retain = !databases || databases.some(db => db.name === "feedseek-reader");
      } catch {
        // Unknown storage state: preserve access rather than strand history.
        retain = true;
      }
    }
    if (retain) {
      const showNotice = () => {
        const notice = globalThis.document?.getElementById("legacyReaderNotice");
        const recovery = globalThis.document?.getElementById("legacyReaderRecovery");
        const newReader = globalThis.document?.getElementById("legacyReaderTarget");
        if (newReader) newReader.href = target;
        if (notice) notice.hidden = false;
        if (recovery) recovery.hidden = true;
      };
      if (globalThis.document?.readyState === "loading") {
        globalThis.document.addEventListener("DOMContentLoaded", showNotice, { once: true });
      } else {
        showNotice();
      }
      return false;
    }
  }
  location.replace(target);
  return true;
})();
