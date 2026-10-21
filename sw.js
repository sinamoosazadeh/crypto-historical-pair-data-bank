const CACHE_NAME = 'crypto-pair-data-bank-shell-v3';
const APP_SHELL = [
  './', './index.html', './manifest.webmanifest',
  './web/assets/app.css', './web/assets/app.js', './web/assets/catalog.js', './web/assets/icon.svg',
  './catalog/sources.json', './catalog/assets.json', './catalog/timeframes.json', './catalog/download-resources.json'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin) return;
  event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
    if (response.ok && response.type === 'basic') {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
    }
    return response;
  }).catch(() => request.mode === 'navigate' ? caches.match('./index.html') : Promise.reject(new Error('Offline and resource not cached')))));
});
