// Wordwise service worker: precache everything, then serve from cache
// (stale-while-revalidate). Bump CACHE when shipping new assets or words.json.
const CACHE = "wordwise-v6";
const ASSETS = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "words.json",
  "icon.svg",
  "icon-192.png",
  "icon-512.png",
  "icon-maskable-512.png",
  "apple-touch-icon.png",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    caches.open(CACHE).then(async (cache) => {
      const cached = await cache.match(req, { ignoreSearch: true });
      const refresh = fetch(req)
        .then((res) => {
          if (res && res.ok) cache.put(req, res.clone());
          return res;
        })
        .catch(() => null);
      if (cached) {
        e.waitUntil(refresh);
        return cached;
      }
      const res = await refresh;
      if (res) return res;
      if (req.mode === "navigate") return (await cache.match("index.html")) || Response.error();
      return Response.error();
    })
  );
});
