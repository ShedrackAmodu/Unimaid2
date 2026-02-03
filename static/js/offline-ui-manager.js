/**
 * Offline UI Manager
 * Manages offline status indicators and sync UI controls
 */

class OfflineUIManager {
  constructor() {
    this.isOnline = navigator.onLine;
    this.pendingCount = 0;
    this.init();
  }

  /**
   * Initialize UI manager
   */
  async init() {
    this.setupListeners();
    this.createOfflineUI();
    this.updateOfflineStatus();
    console.log('✅ Offline UI Manager initialized');
  }

  /**
   * Setup event listeners
   */
  setupListeners() {
    // Listen for offline status changes
    window.addEventListener('offlineStatusChange', (event) => {
      this.isOnline = event.detail.isOnline;
      this.updateOfflineStatus();
      this.updateIndicators();
    });

    // Listen for sync completion
    window.addEventListener('offlineSyncComplete', (event) => {
      this.showSyncNotification(event.detail);
    });

    // Check periodically for pending requests
    setInterval(() => {
      this.updatePendingCount();
    }, 5000);
  }

  /**
   * Create offline UI elements
   */
  createOfflineUI() {
    // Create offline status badge
    const statusBadge = document.createElement('div');
    statusBadge.id = 'offline-status-badge';
    statusBadge.className = 'offline-status-badge online';
    statusBadge.innerHTML = `
      <div class="status-content">
        <span class="status-icon">
          <i class="bi bi-wifi"></i>
        </span>
        <span class="status-text">Online</span>
      </div>
    `;
    statusBadge.style.cssText = `
      position: fixed;
      top: 70px;
      right: 20px;
      z-index: 1000;
      background: white;
      border: 2px solid #22c55e;
      border-radius: 20px;
      padding: 8px 16px;
      font-size: 14px;
      font-weight: 600;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.3s ease;
    `;

    // Create sync controls panel
    const syncPanel = document.createElement('div');
    syncPanel.id = 'offline-sync-panel';
    syncPanel.className = 'offline-sync-panel hidden';
    syncPanel.innerHTML = `
      <div class="sync-panel-content">
        <div class="sync-header">
          <h6 class="mb-0">
            <i class="bi bi-cloud-check"></i> Offline Mode
          </h6>
          <button class="btn-close btn-sm" onclick="this.closest('.offline-sync-panel').classList.add('hidden')"></button>
        </div>
        <div class="sync-body">
          <p class="text-muted small mb-3">You have <strong id="pending-count">0</strong> pending changes</p>
          <div class="progress mb-3" id="sync-progress" style="display: none;">
            <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
          </div>
          <div id="sync-status-message" class="text-muted small mb-3"></div>
          <button class="btn btn-sm btn-primary w-100" id="manual-sync-btn" onclick="window.OfflineRequestInterceptor?.manualSync()">
            <i class="bi bi-arrow-clockwise"></i> Sync Now
          </button>
        </div>
        <div class="sync-footer text-muted small">
          <p class="mb-0">Changes will sync automatically when online</p>
        </div>
      </div>
    `;
    syncPanel.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 1000;
      background: white;
      border: 2px solid #f59e0b;
      border-radius: 12px;
      padding: 0;
      width: 320px;
      max-width: 90vw;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
      transition: all 0.3s ease;
    `;
    syncPanel.classList.add('hidden');
    syncPanel.style.display = 'none';

    // Add styles for hidden state
    const style = document.createElement('style');
    style.textContent = `
      .offline-sync-panel {
        opacity: 1;
        transform: translateY(0);
        transition: all 0.3s ease;
      }

      .offline-sync-panel.hidden {
        opacity: 0;
        transform: translateY(400px);
        pointer-events: none;
      }

      .sync-panel-content {
        padding: 12px;
      }

      .sync-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid #e5e7eb;
      }

      .sync-header h6 {
        color: #f59e0b;
        margin: 0;
        font-size: 14px;
      }

      .sync-body {
        min-height: 80px;
      }

      .sync-footer {
        padding-top: 8px;
        border-top: 1px solid #e5e7eb;
        text-align: center;
      }

      .offline-status-badge {
        color: #22c55e;
      }

      .offline-status-badge.offline {
        color: #ef4444;
        border-color: #ef4444;
      }

      .offline-status-badge.offline .status-text::after {
        content: ' (offline)';
      }

      .status-content {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .status-icon {
        font-size: 16px;
      }

      .status-icon i {
        animation: pulse 2s infinite;
      }

      @keyframes pulse {
        0%, 100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }

      /* Dark mode support */
      [data-theme="dark"] .offline-status-badge,
      [data-theme="dark"] .offline-sync-panel {
        background: #1f2937;
        color: #f8f9fa;
        border-color: #374151;
      }

      [data-theme="dark"] .offline-status-badge.offline {
        border-color: #ef4444;
        color: #ef4444;
      }

      [data-theme="dark"] .sync-header,
      [data-theme="dark"] .sync-footer {
        border-color: #374151;
      }

      [data-theme="dark"] .sync-header h6 {
        color: #fbbf24;
      }

      [data-theme="dark"] .text-muted {
        color: #9ca3af !important;
      }
    `;
    document.head.appendChild(style);

    document.body.appendChild(statusBadge);
    document.body.appendChild(syncPanel);
  }

  /**
   * Update offline status display
   */
  updateOfflineStatus() {
    const badge = document.getElementById('offline-status-badge');
    const panel = document.getElementById('offline-sync-panel');

    if (!badge || !panel) return;

    if (this.isOnline) {
      badge.classList.remove('offline');
      badge.classList.add('online');
      badge.querySelector('.status-text').textContent = 'Online';
      badge.querySelector('.status-icon i').className = 'bi bi-wifi';

      // Hide sync panel if no pending items
      if (this.pendingCount === 0) {
        panel.classList.add('hidden');
        panel.style.display = 'none';
      }
    } else {
      badge.classList.remove('online');
      badge.classList.add('offline');
      badge.querySelector('.status-text').textContent = 'Offline';
      badge.querySelector('.status-icon i').className = 'bi bi-exclamation-circle-fill';

      // Show sync panel with pending count
      panel.classList.remove('hidden');
      panel.style.display = 'block';
      this.updatePendingDisplay();
    }
  }

  /**
   * Update indicators
   */
  updateIndicators() {
    // Could trigger other UI updates here
    const event = new CustomEvent('offlineUIUpdated', {
      detail: {
        isOnline: this.isOnline,
        pendingCount: this.pendingCount,
        timestamp: Date.now(),
      },
    });
    window.dispatchEvent(event);
  }

  /**
   * Update pending request count
   */
  async updatePendingCount() {
    if (!window.OfflineRequestInterceptor) return;

    const count = await window.OfflineRequestInterceptor.getPendingCount();
    if (count !== this.pendingCount) {
      this.pendingCount = count;
      this.updatePendingDisplay();
    }
  }

  /**
   * Update pending display
   */
  updatePendingDisplay() {
    const badge = document.getElementById('pending-count');
    if (badge) {
      badge.textContent = this.pendingCount;
    }

    const panel = document.getElementById('offline-sync-panel');
    if (panel && !this.isOnline && this.pendingCount > 0) {
      panel.classList.remove('hidden');
      panel.style.display = 'block';
    }
  }

  /**
   * Show sync notification
   */
  showSyncNotification(data) {
    const { successCount, failureCount } = data;
    const total = successCount + failureCount;

    let message = '';
    let type = 'success';

    if (successCount === total) {
      message = `✅ Synced all ${total} pending changes`;
    } else if (failureCount === total) {
      message = `⚠️ Failed to sync ${total} changes. Will retry soon.`;
      type = 'warning';
    } else {
      message = `⚠️ Synced ${successCount} of ${total} changes. ${failureCount} will retry.`;
      type = 'info';
    }

    this.showToast(message, type);

    // Update pending count
    this.pendingCount = failureCount;
    this.updatePendingDisplay();

    // Close panel if all synced
    if (failureCount === 0) {
      const panel = document.getElementById('offline-sync-panel');
      if (panel) {
        panel.classList.add('hidden');
        panel.style.display = 'none';
      }
    }
  }

  /**
   * Show toast notification
   */
  showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = `
      top: 20px;
      left: 20px;
      z-index: 1050;
      min-width: 300px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    toast.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      toast.remove();
    }, 5000);
  }

  /**
   * Get storage info
   */
  async getStorageInfo() {
    if (!window.OfflineRequestInterceptor) return null;
    return window.OfflineRequestInterceptor.getStorageStatus();
  }

  /**
   * Show storage info
   */
  async showStorageInfo() {
    const info = await this.getStorageInfo();
    if (!info) return;

    const percentageUsed = info.percentage || 0;
    const msgType = percentageUsed > 80 ? 'warning' : 'info';

    let message = `📦 Storage: ${(info.usage / (1024 * 1024)).toFixed(2)}MB / ${(info.quota / (1024 * 1024)).toFixed(2)}MB (${percentageUsed}%)`;
    if (info.pendingRequests > 0) {
      message += ` | 📋 Pending: ${info.pendingRequests}`;
    }

    this.showToast(message, msgType);
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.OfflineUIManager = new OfflineUIManager();
  });
} else {
  window.OfflineUIManager = new OfflineUIManager();
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = OfflineUIManager;
}
