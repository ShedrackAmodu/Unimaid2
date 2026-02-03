/**
 * Offline Data Manager
 * Handles IndexedDB storage and sync queue for offline-first application
 * Automatically syncs when back online
 */

class OfflineDataManager {
  constructor() {
    this.DB_NAME = 'ramat-library-db';
    this.DB_VERSION = 2;
    this.STORES = {
      'pages': 'url',          // Cached HTML pages
      'api-data': 'endpoint',  // API responses
      'sync-queue': '++id',    // Queue of failed requests to retry
      'user-data': 'key',      // User info, preferences
    };
    this.db = null;
    this.isSyncing = false;
    this.syncInterval = 30000; // Retry sync every 30 seconds
    this.init();
  }

  /**
   * Initialize IndexedDB
   */
  async init() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

      request.onerror = () => {
        console.error('❌ IndexedDB open error:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('✅ IndexedDB initialized:', this.DB_NAME);
        this.setupOnlineListener();
        this.startAutoSync();
        resolve(this.db);
      };

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        console.log('📦 Upgrading IndexedDB schema...');

        // Create object stores if they don't exist
        Object.keys(this.STORES).forEach(storeName => {
          if (!db.objectStoreNames.contains(storeName)) {
            const store = db.createObjectStore(storeName, { keyPath: this.STORES[storeName] });
            
            // Add indices
            if (storeName === 'sync-queue') {
              store.createIndex('status', 'status', { unique: false });
              store.createIndex('timestamp', 'timestamp', { unique: false });
            }
            if (storeName === 'api-data') {
              store.createIndex('timestamp', 'timestamp', { unique: false });
              store.createIndex('expiry', 'expiry', { unique: false });
            }
            console.log(`  ✅ Created store: ${storeName}`);
          }
        });
      };
    });
  }

  /**
   * Save page to cache
   */
  async savePage(url, html) {
    if (!this.db) return;
    const transaction = this.db.transaction(['pages'], 'readwrite');
    const store = transaction.objectStore('pages');
    
    return new Promise((resolve, reject) => {
      const request = store.put({
        url,
        html,
        timestamp: Date.now(),
      });

      request.onsuccess = () => {
        console.log(`✅ Cached page: ${url}`);
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get cached page
   */
  async getPage(url) {
    if (!this.db) return null;
    const transaction = this.db.transaction(['pages'], 'readonly');
    const store = transaction.objectStore('pages');

    return new Promise((resolve, reject) => {
      const request = store.get(url);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Save API data with expiry
   */
  async saveAPIData(endpoint, data, ttl = 3600000) {
    if (!this.db) return;
    const transaction = this.db.transaction(['api-data'], 'readwrite');
    const store = transaction.objectStore('api-data');
    
    return new Promise((resolve, reject) => {
      const request = store.put({
        endpoint,
        data,
        timestamp: Date.now(),
        expiry: Date.now() + ttl,
      });

      request.onsuccess = () => {
        console.log(`✅ Cached API data: ${endpoint}`);
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get cached API data (if not expired)
   */
  async getAPIData(endpoint) {
    if (!this.db) return null;
    const transaction = this.db.transaction(['api-data'], 'readonly');
    const store = transaction.objectStore('api-data');

    return new Promise((resolve, reject) => {
      const request = store.get(endpoint);
      request.onsuccess = () => {
        const result = request.result;
        if (result && result.expiry > Date.now()) {
          console.log(`✅ Using cached API data: ${endpoint}`);
          resolve(result.data);
        } else if (result) {
          // Data expired, delete it
          this.deleteAPIData(endpoint);
          resolve(null);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Delete cached API data
   */
  async deleteAPIData(endpoint) {
    if (!this.db) return;
    const transaction = this.db.transaction(['api-data'], 'readwrite');
    const store = transaction.objectStore('api-data');
    
    return new Promise((resolve, reject) => {
      const request = store.delete(endpoint);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Add request to sync queue
   */
  async queueRequest(method, url, data = null, headers = {}) {
    if (!this.db) return;
    const transaction = this.db.transaction(['sync-queue'], 'readwrite');
    const store = transaction.objectStore('sync-queue');

    return new Promise((resolve, reject) => {
      const request = store.add({
        method,
        url,
        data,
        headers,
        timestamp: Date.now(),
        status: 'pending',
        attempts: 0,
      });

      request.onsuccess = () => {
        console.log(`✅ Queued request: ${method} ${url}`);
        resolve(request.result);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get all pending sync requests
   */
  async getPendingRequests() {
    if (!this.db) return [];
    const transaction = this.db.transaction(['sync-queue'], 'readonly');
    const store = transaction.objectStore('sync-queue');
    const index = store.index('status');

    return new Promise((resolve, reject) => {
      const request = index.getAll('pending');
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Update sync queue item
   */
  async updateQueueItem(id, updates) {
    if (!this.db) return;
    const transaction = this.db.transaction(['sync-queue'], 'readwrite');
    const store = transaction.objectStore('sync-queue');

    return new Promise((resolve, reject) => {
      const getRequest = store.get(id);
      
      getRequest.onsuccess = () => {
        const item = getRequest.result;
        const updated = { ...item, ...updates };
        const putRequest = store.put(updated);
        
        putRequest.onsuccess = () => resolve();
        putRequest.onerror = () => reject(putRequest.error);
      };
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  /**
   * Remove sync queue item
   */
  async removeQueueItem(id) {
    if (!this.db) return;
    const transaction = this.db.transaction(['sync-queue'], 'readwrite');
    const store = transaction.objectStore('sync-queue');

    return new Promise((resolve, reject) => {
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Sync all pending requests
   */
  async syncPendingRequests() {
    if (this.isSyncing) {
      console.log('⏳ Sync already in progress...');
      return;
    }

    if (!navigator.onLine) {
      console.log('📡 Still offline, skipping sync');
      return;
    }

    this.isSyncing = true;
    console.log('🔄 Starting sync of pending requests...');

    try {
      const requests = await this.getPendingRequests();
      console.log(`📋 Found ${requests.length} pending requests`);

      let successCount = 0;
      let failureCount = 0;

      for (const item of requests) {
        try {
          const response = await fetch(item.url, {
            method: item.method,
            headers: {
              'Content-Type': 'application/json',
              ...item.headers,
            },
            body: item.data ? JSON.stringify(item.data) : null,
          });

          if (response.ok) {
            await this.removeQueueItem(item.id);
            successCount++;
            console.log(`✅ Synced: ${item.method} ${item.url}`);
          } else {
            // Increment attempts and keep in queue
            await this.updateQueueItem(item.id, {
              attempts: item.attempts + 1,
              lastError: response.statusText,
            });
            failureCount++;
            console.warn(`⚠️ Failed: ${item.method} ${item.url} - ${response.statusText}`);
          }
        } catch (error) {
          console.error(`❌ Sync error: ${item.method} ${item.url}`, error);
          failureCount++;
          await this.updateQueueItem(item.id, {
            attempts: item.attempts + 1,
            lastError: error.message,
          });
        }
      }

      console.log(`🎯 Sync complete: ${successCount} succeeded, ${failureCount} failed`);
      this.broadcastSyncStatus(successCount, failureCount);
    } catch (error) {
      console.error('❌ Sync failed:', error);
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Setup online listener for auto-sync
   */
  setupOnlineListener() {
    window.addEventListener('online', async () => {
      console.log('📡 Back online! Starting sync...');
      await this.syncPendingRequests();
    });
  }

  /**
   * Start auto-sync interval
   */
  startAutoSync() {
    setInterval(async () => {
      if (navigator.onLine) {
        await this.syncPendingRequests();
      }
    }, this.syncInterval);
  }

  /**
   * Broadcast sync status to all open tabs
   */
  broadcastSyncStatus(successCount, failureCount) {
    const channel = new BroadcastChannel('offline-sync');
    channel.postMessage({
      type: 'SYNC_COMPLETE',
      successCount,
      failureCount,
      timestamp: Date.now(),
    });
    channel.close();
  }

  /**
   * Save user data
   */
  async saveUserData(key, value) {
    if (!this.db) return;
    const transaction = this.db.transaction(['user-data'], 'readwrite');
    const store = transaction.objectStore('user-data');

    return new Promise((resolve, reject) => {
      const request = store.put({ key, value, timestamp: Date.now() });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Get user data
   */
  async getUserData(key) {
    if (!this.db) return null;
    const transaction = this.db.transaction(['user-data'], 'readonly');
    const store = transaction.objectStore('user-data');

    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => {
        const result = request.result;
        resolve(result ? result.value : null);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * Clear all data
   */
  async clearAll() {
    if (!this.db) return;
    const storeNames = Object.keys(this.STORES);

    for (const storeName of storeNames) {
      const transaction = this.db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);

      await new Promise((resolve, reject) => {
        const request = store.clear();
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
      });
    }

    console.log('✅ All offline data cleared');
  }

  /**
   * Get storage stats
   */
  async getStorageStats() {
    if (!navigator.storage || !navigator.storage.estimate) return null;
    const estimate = await navigator.storage.estimate();
    return {
      usage: estimate.usage,
      quota: estimate.quota,
      percentage: Math.round((estimate.usage / estimate.quota) * 100),
    };
  }
}

// Create global instance
window.OfflineDataManager = OfflineDataManager;
if (typeof module !== 'undefined' && module.exports) {
  module.exports = OfflineDataManager;
}
