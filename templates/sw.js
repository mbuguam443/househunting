const CACHE = 'pata-v1';
const STATIC = [
  '/static/css/style.css',
  '/static/css/bootstrap.min.css',
  '/static/css/all.min.css',
  '/static/js/bootstrap.bundle.min.js',
  '/static/js/jquery-3.7.1.min.js',
  '/static/img/icon-192.png',
  '/static/img/icon-512.png',
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(STATIC))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
