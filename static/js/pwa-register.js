// Register service worker and handle updates
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/static/js/service-worker.js', { scope: '/' })
      .then(registration => {
        console.log('Service Worker registered successfully:', registration);

        // Check for updates periodically (every hour)
        setInterval(() => {
          registration.update();
        }, 3600000);

        // Listen for updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          newWorker.addEventListener('statechange', () => {
            if (
              newWorker.state === 'installed' &&
              navigator.serviceWorker.controller
            ) {
              // New service worker is ready
              console.log('New service worker available');
              showUpdatePrompt();
            }
          });
        });
      })
      .catch(error => {
        console.error('Service Worker registration failed:', error);
      });

    // Handle service worker messages
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.addEventListener('message', event => {
        if (event.data && event.data.type === 'CACHE_UPDATED') {
          console.log('Cache updated by service worker');
        }
      });
    }
  });

  // Listen for controller changes
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    console.log('Service Worker controller changed');
  });
}

// Function to show update prompt
function showUpdatePrompt() {
  const updateNotification = document.createElement('div');
  updateNotification.className = 'alert alert-info alert-dismissible fade show position-fixed';
  updateNotification.style.cssText = `
    top: 20px;
    right: 20px;
    z-index: 9999;
    min-width: 300px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  `;
  updateNotification.innerHTML = `
    <strong>Update Available!</strong> A new version of the app is ready.
    <button type="button" class="btn btn-sm btn-primary" id="update-btn">Update Now</button>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;

  document.body.appendChild(updateNotification);

  document.getElementById('update-btn').addEventListener('click', () => {
    // Reload the page to get the new service worker
    window.location.reload();
  });
}

// Detect when offline
window.addEventListener('offline', () => {
  console.log('App is offline');
  showOfflineNotification();
});

// Detect when back online
window.addEventListener('online', () => {
  console.log('App is back online');
  hideOfflineNotification();
});

function showOfflineNotification() {
  if (!document.getElementById('offline-notification')) {
    const notification = document.createElement('div');
    notification.id = 'offline-notification';
    notification.className = 'alert alert-warning alert-dismissible fade show position-fixed';
    notification.style.cssText = `
      bottom: 20px;
      left: 20px;
      z-index: 9999;
      min-width: 300px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    `;
    notification.innerHTML = `
      <strong>You are offline</strong> - Using cached content.
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(notification);
  }
}

function hideOfflineNotification() {
  const notification = document.getElementById('offline-notification');
  if (notification) {
    notification.remove();
  }
}

// Check if app is installed
window.addEventListener('beforeinstallprompt', e => {
  // Prevent the mini-infobar from appearing on mobile
  e.preventDefault();
  // Stash the event for later use.
  let deferredPrompt = e;

  // Show install button if not already installed
  const installBtn = document.getElementById('install-app-btn');
  if (installBtn) {
    installBtn.style.display = 'block';
    installBtn.addEventListener('click', async () => {
      // Show the install prompt.
      deferredPrompt.prompt();
      // Log the result
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User response to the install prompt: ${outcome}`);
      // Clear the deferredPrompt for the next time.
      deferredPrompt = null;
    });
  }
});

// Detect when app is installed
window.addEventListener('appinstalled', () => {
  console.log('PWA app installed successfully');
  const installBtn = document.getElementById('install-app-btn');
  if (installBtn) {
    installBtn.style.display = 'none';
  }
});
