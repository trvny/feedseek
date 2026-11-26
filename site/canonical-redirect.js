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
  location.replace("https://rss.bartek.lol" + routes[location.pathname] + location.search + location.hash);
})();
