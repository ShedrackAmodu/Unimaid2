/**
 * PWA Install Handler
 * Manages the install prompt and provides user feedback for PWA installation
 */

let deferredPrompt = null;
const installButton = document.getElementById('install-app-btn');

/**
 * Handle the beforeinstallprompt event
 * This event fires when the browser detects the app is installable
 */
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Store the event for later use
  deferredPrompt = e;

  // Show the install button
  if (installButton) {
    installButton.style.display = 'inline-block';
    installButton.addEventListener('click', handleInstallClick);
  }

  console.log('PWA install prompt is ready');
});

/**
 * Handle install button click
 */
async function handleInstallClick(e) {
  e.preventDefault();

  if (!deferredPrompt) {
    console.warn('Install prompt is not available');
    showInstallNotification('Install not available', 'Please try again later', 'warning');
    return;
  }

  try {
    // Show the install prompt
    deferredPrompt.prompt();

    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;

    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
      showInstallNotification('Success!', 'App installed successfully. You can now access it from your home screen.', 'success');
    } else {
      console.log('User dismissed the install prompt');
    }

    // Clear the deferredPrompt for the next time
    deferredPrompt = null;
  } catch (error) {
    console.error('Error during installation:', error);
    showInstallNotification('Installation Error', 'An error occurred during installation. Please try again.', 'danger');
  }
}

/**
 * Handle when the app is successfully installed
 */
window.addEventListener('appinstalled', () => {
  console.log('PWA app installed successfully');

  // Hide the install button
  if (installButton) {
    installButton.style.display = 'none';
  }

  // Clear the deferredPrompt
  deferredPrompt = null;

  // Show a success notification
  showInstallNotification('App Installed', 'The Ramat Library app has been added to your home screen!', 'success');
});

/**
 * Check if the app is running in standalone mode (already installed)
 */
function isAppInstalled() {
  // Check if running in standalone mode
  if (window.navigator.standalone === true) {
    return true;
  }

  // Check if running in PWA display mode
  if (window.matchMedia('(display-mode: standalone)').matches) {
    return true;
  }

  return false;
}

/**
 * Show installation notification
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 * @param {string} type - Alert type (success, warning, danger, info)
 */
function showInstallNotification(title, message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.cssText = `
    top: 20px;
    right: 20px;
    z-index: 9999;
    min-width: 300px;
    max-width: 400px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  `;
  notification.innerHTML = `
    <strong>${title}</strong><br/>
    <small>${message}</small>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
  `;

  document.body.appendChild(notification);

  // Auto-dismiss after 5 seconds
  setTimeout(() => {
    const bsAlert = new bootstrap.Alert(notification);
    bsAlert.close();
  }, 5000);
}

/**
 * Check installation status on page load
 */
document.addEventListener('DOMContentLoaded', () => {
  if (isAppInstalled()) {
    // App is already installed, hide the button
    if (installButton) {
      installButton.style.display = 'none';
    }
    console.log('App is already installed');
  }
});

/**
 * Provide alternative installation methods for iOS
 */
function showIOSInstallGuide() {
  const iosGuide = document.createElement('div');
  iosGuide.className = 'modal fade';
  iosGuide.id = 'iosInstallModal';
  iosGuide.setAttribute('tabindex', '-1');
  iosGuide.innerHTML = `
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Install Ramat Library on iOS</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p>To install this app on your iPhone or iPad:</p>
          <ol>
            <li>Tap the <strong>Share</strong> button at the bottom of Safari</li>
            <li>Scroll down and tap <strong>Add to Home Screen</strong></li>
            <li>Choose a name for the app and tap <strong>Add</strong></li>
            <li>The app will now appear on your home screen</li>
          </ol>
          <div class="alert alert-info mt-3">
            <small>Note: Make sure you're using Safari browser for the best experience.</small>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(iosGuide);
  return new bootstrap.Modal(iosGuide);
}

/**
 * Detect iOS and provide appropriate installation method
 */
function detectIOSAndShowGuide() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isStandalone = window.navigator.standalone === true;

  if (isIOS && !isStandalone) {
    // iOS device that hasn't installed the app yet
    if (installButton) {
      const originalClick = installButton.onclick;
      installButton.onclick = (e) => {
        e.preventDefault();
        if (deferredPrompt) {
          handleInstallClick(e);
        } else {
          const modal = showIOSInstallGuide();
          modal.show();
        }
      };
    }
  }
}

// Initialize iOS detection on page load
document.addEventListener('DOMContentLoaded', detectIOSAndShowGuide);

// Export functions for external use
window.PWAInstaller = {
  showIOSGuide: () => {
    const modal = showIOSInstallGuide();
    modal.show();
  },
  isInstalled: isAppInstalled,
  showNotification: showInstallNotification,
};
