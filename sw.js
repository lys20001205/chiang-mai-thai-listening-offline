const CACHE = 'chiangmai-ear-shell-v5';
const ROOT = self.registration.scope;
const SHELL = new URL('./index.html', ROOT).href;
const PRACTICE = new URL('./practice.html', ROOT).href;
const MANIFEST = new URL('./manifest.webmanifest', ROOT).href;
const ASSETS = [ROOT, SHELL, PRACTICE, MANIFEST];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll(ASSETS);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith('chiangmai-ear-shell-') && key !== CACHE).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || request.mode !== 'navigate') return;
  const url = new URL(request.url);
  url.search = '';
  url.hash = '';
  // Match known pages only. An offline practice URL must never become the old home page.
  if (!ASSETS.includes(url.href)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const response = await fetch(request);
      if (response.ok) {
        try { await cache.put(url.href, response.clone()); } catch (_) { /* A full cache must not hide a valid online response. */ }
        return response;
      }
      return (await cache.match(url.href)) || response;
    } catch (_) {
      return (await cache.match(url.href)) || Response.error();
    }
  })());
});
