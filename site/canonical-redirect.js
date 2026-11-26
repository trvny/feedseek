(() => {
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
    if (retain) {
      globalThis.document?.addEventListener("DOMContentLoaded", () => {
        const notice = document.getElementById("legacyReaderNotice");
        if (notice) notice.hidden = false;
      });
      return;
    }
  }
  location.replace(target);
})();
