const CACHE_NAME = 'ramat-library-v2';
const API_CACHE = 'ramat-library-api-v1';
const STATIC_CACHE = 'ramat-library-static-v1';

const urlsToCache = [
  '/',
  '/offline/',
  '/static/css/site-responsive.css',
  '/static/css/dark-theme.css',
  '/static/css/professional-base.css',
  '/static/css/theme-enhancements.css',
  '/static/css/responsive-advanced.css',
  '/static/images/librarybooks.jfif',
  '/static/js/service-worker.js',
  '/static/js/offline-data-manager.js',
  '/static/js/pwa-register.js',
  '/static/js/utilities.js',
  '/static/js/theme-manager.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css',
  'https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css',
];

// ============================================================================
// INSTALL EVENT - Cache all essential assets
// ============================================================================
self.addEventListener('install', event => {
  console.log('📦 Service Worker installing...');
  event.waitUntil(
    Promise.all([
      // Cache static assets
      caches.open(STATIC_CACHE).then(cache => {
        console.log('📚 Caching static assets');
        return cache.addAll(urlsToCache).catch(err => {
          console.warn('⚠️ Some resources failed to cache:', err);
          return Promise.resolve();
        });
      }),
      // Create API cache for later use
      caches.open(API_CACHE).then(() => {
        console.log('✅ API cache ready');
      }),
    ])
  );
  self.skipWaiting();
});

// ============================================================================
// ACTIVATE EVENT - Clean up old caches
// ============================================================================
self.addEventListener('activate', event => {
  console.log('🚀 Service Worker activating...');
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          const isCurrentCache = [CACHE_NAME, STATIC_CACHE, API_CACHE].includes(cacheName);
          if (!isCurrentCache) {
            console.log(`🗑️ Deleting old cache: ${cacheName}`);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// ============================================================================
// FETCH EVENT - Cache Strategy with Offline Support
// ============================================================================
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome extensions
  if (request.url.startsWith('chrome-extension://')) {
    return;
  }

  // ========================================================================
  // API REQUESTS - Network first with cache fallback
  // ========================================================================
  if (url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Validate response
          if (!response || response.status !== 200) {
            return response;
          }

          // Clone for caching
          const clonedResponse = response.clone();

          // Store in IndexedDB via message (if available)
          const endpoint = url.pathname;
          if (self.clients) {
            self.clients.matchAll().then(clients => {
              clients.forEach(client => {
                client.postMessage({
                  type: 'CACHE_API',
                  endpoint,
                  data: response.json(),
                });
              });
            });
          }

          // Also cache in browser cache
          caches.open(API_CACHE).then(cache => {
            cache.put(request, clonedResponse);
          });

          return response;
        })
        .catch(() => {
          // Network failed - try cache
          return caches.match(request).then(cachedResponse => {
            if (cachedResponse) {
              console.log(`✅ Using cached API response: ${url.pathname}`);
              return cachedResponse;
            }

            // Return offline response
            return new Response(
              JSON.stringify({
                error: 'offline',
                message: 'You are offline. Please check your connection.',
                cached: false,
                timestamp: Date.now(),
              }),
              {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({ 'Content-Type': 'application/json' }),
              }
            );
          });
        })
    );
    return;
  }

  // ========================================================================
  // STATIC ASSETS - Cache first with network fallback
  // ========================================================================
  if (
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.woff') ||
    url.pathname.endsWith('.woff2') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.jpeg') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.gif')
  ) {
    event.respondWith(
      caches.match(request).then(response => {
        if (response) {
          // Cache hit, but update in background
          fetch(request).then(updatedResponse => {
            if (updatedResponse && updatedResponse.status === 200) {
              caches.open(STATIC_CACHE).then(cache => {
                cache.put(request, updatedResponse);
              });
            }
          }).catch(() => {
            // Background update failed, use cache
          });
          return response;
        }

        // Not in cache, try network
        return fetch(request)
          .then(response => {
            if (!response || response.status !== 200) {
              return response;
            }

            const clonedResponse = response.clone();
            caches.open(STATIC_CACHE).then(cache => {
              cache.put(request, clonedResponse);
            });

            return response;
          })
          .catch(() => {
            // Return placeholder for missing images
            if (url.pathname.match(/\.(png|jpg|jpeg|svg|gif)$/i)) {
              return new Response(
                '<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg"><rect fill="#f0f0f0" width="200" height="200"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999">Offline</text></svg>',
                { headers: { 'Content-Type': 'image/svg+xml' } }
              );
            }
            return new Response('Resource not available', { status: 404 });
          });
      })
    );
    return;
  }

  // ========================================================================
  // HTML PAGES - Network first with cache fallback
  // ========================================================================
  event.respondWith(
    fetch(request)
      .then(response => {
        if (!response || response.status !== 200 || response.type === 'error') {
          return response;
        }

        // Clone the response
        const clonedResponse = response.clone();

        // Cache HTML pages
        caches.open(CACHE_NAME).then(cache => {
          cache.put(request, clonedResponse);
        });

        return response;
      })
      .catch(() => {
        // Network failed - try cache
        return caches.match(request).then(cachedResponse => {
          if (cachedResponse) {
            console.log(`✅ Using cached page: ${url.pathname}`);
            return cachedResponse;
          }

          // Return offline page as fallback
          return caches.match('/offline/').then(offlinePage => {
            return offlinePage || new Response(
              '<h1>Offline</h1><p>This page is not available offline. Please check your connection.</p>',
              { headers: { 'Content-Type': 'text/html' } }
            );
          });
        });
      })
  );
});

// ============================================================================
// MESSAGE HANDLER - Handle messages from clients
// ============================================================================
self.addEventListener('message', event => {
  const { data } = event;

  // Skip waiting and activate new worker
  if (data && data.type === 'SKIP_WAITING') {
    self.skipWaiting();
    console.log('⏭️ Skipping waiting for new service worker');
  }

  // Clear all caches
  if (data && data.type === 'CLEAR_CACHE') {
    caches.keys().then(cacheNames => {
      Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
      ).then(() => {
        console.log('✅ All caches cleared');
        event.ports[0].postMessage({ success: true });
      });
    });
  }

  // Get cache stats
  if (data && data.type === 'GET_CACHE_STATS') {
    caches.keys().then(cacheNames => {
      const stats = {};
      Promise.all(
        cacheNames.map(cacheName =>
          caches.open(cacheName).then(cache => {
            cache.keys().then(keys => {
              stats[cacheName] = keys.length;
            });
          })
        )
      ).then(() => {
        event.ports[0].postMessage({ stats });
      });
    });
  }

  // Queue offline request
  if (data && data.type === 'QUEUE_REQUEST') {
    console.log('📋 Queuing offline request:', data.url);
    // Data will be queued by OfflineDataManager on the client side
  }

  // Trigger sync
  if (data && data.type === 'TRIGGER_SYNC') {
    console.log('🔄 Triggering sync from client');
    // Notify all clients about sync
    self.clients.matchAll().then(clients => {
      clients.forEach(client => {
        client.postMessage({
          type: 'SYNC_REQUEST',
          timestamp: Date.now(),
        });
      });
    });
  }
});

// ============================================================================
// BACKGROUND SYNC (if supported)
// ============================================================================
if ('sync' in self.registration) {
  self.addEventListener('sync', event => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-pending-requests') {
      event.waitUntil(
        self.clients.matchAll().then(clients => {
          clients.forEach(client => {
            client.postMessage({
              type: 'BACKGROUND_SYNC',
              timestamp: Date.now(),
            });
          });
        })
      );
    }
  });
}

console.log('✅ Enhanced Service Worker loaded with offline support');

