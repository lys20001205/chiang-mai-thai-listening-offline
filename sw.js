const CACHE = 'chiangmai-ear-shell-v4';
const ROOT = self.registration.scope;
const SHELL = new URL('./index.html', ROOT).href;
const MANIFEST = new URL('./manifest.webmanifest', ROOT).href;

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await cache.addAll([ROOT, SHELL, MANIFEST]);
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
  if (request.method !== 'GET' || request.mode !== 'navigate' || !request.url.startsWith(ROOT)) return;
  event.respondWith((async () => {
    try {
      const response = await fetch(request);
      if (response.ok) {
        const cache = await caches.open(CACHE);
        event.waitUntil(cache.put(request, response.clone()));
      }
      return response;
    } catch (_) {
      return (await caches.match(request)) || (await caches.match(ROOT)) || (await caches.match(SHELL)) || Response.error();
    }
  })());
});
