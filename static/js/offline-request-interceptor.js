/**
 * Offline Request Interceptor
 * Automatically intercepts fetch requests and queues them when offline
 * Syncs when back online
 */

class OfflineRequestInterceptor {
  constructor(offlineDataManager) {
    this.offlineManager = offlineDataManager;
    this.isOnline = navigator.onLine;
    this.setupListeners();
  }

  /**
   * Setup online/offline listeners
   */
  setupListeners() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      console.log('📡 Back online! Triggering sync...');
      this.broadcastOnlineStatus();
      this.triggerSync();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      console.log('📡 Went offline');
      this.broadcastOnlineStatus();
    });

    // Listen for background sync messages
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', event => {
        if (event.data && event.data.type === 'BACKGROUND_SYNC') {
          console.log('🔄 Background sync message received');
          this.triggerSync();
        }
      });
    }

    // Listen for sync complete messages
    const channel = new BroadcastChannel('offline-sync');
    channel.addEventListener('message', (event) => {
      if (event.data && event.data.type === 'SYNC_COMPLETE') {
        console.log(`✅ Sync complete: ${event.data.successCount} succeeded, ${event.data.failureCount} failed`);
        this.broadcastSyncComplete(event.data);
      }
    });
  }

  /**
   * Wrap fetch to intercept requests
   */
  initializeFetchInterception() {
    const originalFetch = window.fetch;

    window.fetch = async (...args) => {
      const [resource, config] = args;
      const method = (config?.method || 'GET').toUpperCase();
      const url = typeof resource === 'string' ? resource : resource.url;

      // Don't intercept non-API requests or GET requests to non-API endpoints
      if (method === 'GET') {
        return originalFetch.apply(this, args);
      }

      // Don't intercept non-JSON requests
      const isJSON = config?.headers?.['Content-Type']?.includes('application/json') ||
                     config?.body instanceof Object;
      if (!isJSON) {
        return originalFetch.apply(this, args);
      }

      // Try to make the request
      try {
        const response = await originalFetch.apply(this, args);
        
        // If successful, return response
        if (response.ok) {
          return response;
        }

        // If failed but online, return error response
        if (this.isOnline) {
          return response;
        }

        // If failed and offline, queue the request
        console.log(`📋 Request failed and offline, queueing: ${method} ${url}`);
        await this.offlineManager.queueRequest(
          method,
          url,
          config?.body,
          config?.headers
        );

        // Return success response to app (will be synced later)
        return new Response(
          JSON.stringify({
            success: true,
            message: 'Request queued for sync',
            queued: true,
            timestamp: Date.now(),
          }),
          {
            status: 202,
            statusText: 'Accepted',
            headers: new Headers({ 'Content-Type': 'application/json' }),
          }
        );
      } catch (error) {
        // Network error while online - queue it
        if (this.isOnline) {
          console.log(`⚠️ Network error, queueing request: ${method} ${url}`);
          await this.offlineManager.queueRequest(
            method,
            url,
            config?.body,
            config?.headers
          );

          return new Response(
            JSON.stringify({
              success: true,
              message: 'Request queued due to network error',
              queued: true,
              timestamp: Date.now(),
            }),
            {
              status: 202,
              statusText: 'Accepted',
              headers: new Headers({ 'Content-Type': 'application/json' }),
            }
          );
        }

        // Offline - queue the request
        console.log(`📋 Offline request queued: ${method} ${url}`);
        await this.offlineManager.queueRequest(
          method,
          url,
          config?.body,
          config?.headers
        );

        return new Response(
          JSON.stringify({
            success: true,
            message: 'Request queued - you are offline',
            queued: true,
            offline: true,
            timestamp: Date.now(),
          }),
          {
            status: 202,
            statusText: 'Accepted',
            headers: new Headers({ 'Content-Type': 'application/json' }),
          }
        );
      }
    };

    console.log('✅ Fetch interception initialized');
  }

  /**
   * Trigger sync of pending requests
   */
  async triggerSync() {
    console.log('🔄 Triggering sync of pending requests');
    await this.offlineManager.syncPendingRequests();
  }

  /**
   * Broadcast online/offline status to UI
   */
  broadcastOnlineStatus() {
    const event = new CustomEvent('offlineStatusChange', {
      detail: {
        isOnline: this.isOnline,
        timestamp: Date.now(),
      },
    });
    window.dispatchEvent(event);

    // Also update DOM if elements exist
    const offlineIndicator = document.getElementById('offline-status-indicator');
    if (offlineIndicator) {
      offlineIndicator.classList.toggle('offline', !this.isOnline);
      offlineIndicator.classList.toggle('online', this.isOnline);
    }
  }

  /**
   * Broadcast sync completion
   */
  broadcastSyncComplete(data) {
    const event = new CustomEvent('offlineSyncComplete', {
      detail: {
        ...data,
        timestamp: Date.now(),
      },
    });
    window.dispatchEvent(event);
  }

  /**
   * Get pending request count
   */
  async getPendingCount() {
    const requests = await this.offlineManager.getPendingRequests();
    return requests.length;
  }

  /**
   * Manually queue a request
   */
  async queueRequest(method, url, data = null, headers = {}) {
    return this.offlineManager.queueRequest(method, url, data, headers);
  }

  /**
   * Manually sync pending requests
   */
  async manualSync() {
    console.log('🔄 Manual sync triggered by user');
    return this.offlineManager.syncPendingRequests();
  }

  /**
   * Get storage status
   */
  async getStorageStatus() {
    const stats = await this.offlineManager.getStorageStats();
    const pendingCount = await this.getPendingCount();
    return {
      ...stats,
      pendingRequests: pendingCount,
      isOnline: this.isOnline,
    };
  }
}

// Create global instance when offline manager is ready
window.addEventListener('DOMContentLoaded', () => {
  if (typeof OfflineDataManager !== 'undefined') {
    const offlineManager = new OfflineDataManager();
    window.OfflineRequestInterceptor = new OfflineRequestInterceptor(offlineManager);
    window.OfflineRequestInterceptor.initializeFetchInterception();
  }
});

// Also make it available globally
window.initOfflineMode = async function() {
  if (typeof OfflineDataManager !== 'undefined' && !window.OfflineRequestInterceptor) {
    const offlineManager = new OfflineDataManager();
    window.OfflineRequestInterceptor = new OfflineRequestInterceptor(offlineManager);
    window.OfflineRequestInterceptor.initializeFetchInterception();
    console.log('✅ Offline mode initialized');
  }
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = OfflineRequestInterceptor;
}
