/* InternSync service worker (FR-PWA-01 – 03; Increment 3 design, Section 6).
 * - The app shell (the page, the manifest, the icons) is cached at install; built files under /assets/ on first use.
 * - Pages are fetched from the network first, with the cached page as the offline fallback.
 * - API answers are never cached: personal data stays off the device, and nothing is submitted offline.
 * - Push messages carry a title and a link only (NFR-PRV-03). */
const VERSION = "internsync-v1";
const SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icons/icon-192.png", "/icons/icon-512.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(VERSION).then((cache) => cache.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin || url.pathname.startsWith("/api/")) return;
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match("/index.html")));
    return;
  }
  if (url.pathname.startsWith("/assets/") || SHELL.includes(url.pathname)) {
    event.respondWith(
      caches.match(request).then((hit) => hit || fetch(request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          void caches.open(VERSION).then((cache) => cache.put(request, copy));
        }
        return response;
      })),
    );
  }
});

self.addEventListener("push", (event) => {
  let data = { title: "InternSync", link: "/" };
  try {
    data = { ...data, ...event.data.json() };
  } catch {
    /* not JSON: show the default title */
  }
  event.waitUntil(self.registration.showNotification(data.title, {
    icon: "/icons/icon-192.png", badge: "/icons/icon-192.png", data: { link: data.link }, lang: "ar", dir: "auto",
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const link = (event.notification.data && event.notification.data.link) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
      for (const client of windows) {
        if ("focus" in client) {
          client.navigate(link);
          return client.focus();
        }
      }
      return self.clients.openWindow(link);
    }),
  );
});
