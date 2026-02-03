/**
 * Enhanced Theme Manager - Complete Theme System for Ramat Library
 * Handles light/dark theme switching with smooth transitions and persistence
 */

class ThemeManager {
  constructor() {
    this.THEME_KEY = 'ramat-library-theme';
    this.TRANSITION_DURATION = 300;
    this.STORAGE_PREFIX = 'theme_';
    this.init();
  }

  /**
   * Initialize theme manager
   */
  init() {
    // Prevent FOUC (Flash of Unstyled Content)
    this.preventFlash();
    
    // Load saved theme or system preference
    this.loadTheme();
    
    // Setup event listeners
    this.setupEventListeners();
    
    // Watch for system theme changes
    this.watchSystemTheme();
    
    // Apply animations and enhancements
    this.enhanceThemeElements();
    
    console.log('✅ Theme Manager initialized');
  }

  /**
   * Prevent flash of unstyled content
   */
  preventFlash() {
    const root = document.documentElement;
    root.style.transition = 'none';
    root.style.colorScheme = 'light';
  }

  /**
   * Load theme from storage or system preference
   */
  loadTheme() {
    const root = document.documentElement;
    const savedTheme = localStorage.getItem(this.THEME_KEY);
    
    let themeToApply = savedTheme;
    
    if (!themeToApply) {
      // Check system preference
      const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      themeToApply = systemDark ? 'dark' : 'light';
    }
    
    // Apply theme
    this.applyTheme(themeToApply);
    
    // Update UI elements
    setTimeout(() => {
      this.updateThemeUI(themeToApply);
    }, 0);
  }

  /**
   * Apply theme to document
   */
  applyTheme(theme) {
    const root = document.documentElement;
    
    // Validate theme
    if (!['light', 'dark'].includes(theme)) {
      console.warn(`Invalid theme: ${theme}. Using light.`);
      theme = 'light';
    }
    
    // Enable transitions after initial load
    root.style.transition = '';
    
    // Apply theme
    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;
    
    // Save preference
    localStorage.setItem(this.THEME_KEY, theme);
    
    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('themechange', {
      detail: { theme }
    }));
    
    console.log(`🎨 Theme applied: ${theme}`);
  }

  /**
   * Toggle between themes
   */
  toggleTheme() {
    const root = document.documentElement;
    const currentTheme = root.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    this.applyTheme(newTheme);
    this.updateThemeUI(newTheme);
    this.showThemeNotification(newTheme);
  }

  /**
   * Update UI elements to reflect theme
   */
  updateThemeUI(theme) {
    const toggleBtn = document.getElementById('themeToggle');
    
    if (toggleBtn) {
      const icon = toggleBtn.querySelector('i');
      
      if (icon) {
        // Update icon
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
        
        // Update accessibility label
        toggleBtn.setAttribute('aria-label', 
          theme === 'dark' 
            ? 'Switch to light theme' 
            : 'Switch to dark theme'
        );
        
        // Add animation
        icon.style.transform = 'rotate(180deg)';
        setTimeout(() => {
          icon.style.transform = 'rotate(0deg)';
        }, TRANSITION_DURATION);
      }
    }
  }

  /**
   * Show theme change notification
   */
  showThemeNotification(theme) {
    if (typeof showToast !== 'undefined') {
      const message = theme === 'dark' 
        ? '🌙 Dark theme activated' 
        : '☀️ Light theme activated';
      
      showToast('info', message);
    } else {
      console.log(`Theme changed to: ${theme}`);
    }
  }

  /**
   * Setup event listeners for theme toggle
   */
  setupEventListeners() {
    const toggleBtn = document.getElementById('themeToggle');
    
    if (toggleBtn) {
      // Remove old inline onclick if exists
      toggleBtn.onclick = null;
      
      // Add click listener
      toggleBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggleTheme();
      });
      
      // Keyboard shortcut: Alt+T
      document.addEventListener('keydown', (e) => {
        if (e.altKey && e.key === 't') {
          this.toggleTheme();
        }
      });
    }
  }

  /**
   * Watch for system theme changes
   */
  watchSystemTheme() {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    darkModeQuery.addListener((e) => {
      // Only auto-switch if user hasn't saved a preference
      if (!localStorage.getItem(this.THEME_KEY)) {
        const newTheme = e.matches ? 'dark' : 'light';
        this.applyTheme(newTheme);
        this.updateThemeUI(newTheme);
      }
    });
  }

  /**
   * Enhance theme elements with animations
   */
  enhanceThemeElements() {
    // Add smooth transitions to all relevant elements
    this.addTransitionClass();
    
    // Monitor dynamic content
    this.observeDynamicContent();
  }

  /**
   * Add transition class to elements
   */
  addTransitionClass() {
    const style = document.createElement('style');
    style.textContent = `
      * {
        transition-property: background-color, color, border-color, box-shadow;
        transition-duration: 300ms;
        transition-timing-function: ease-in-out;
      }
      
      .theme-transition {
        transition: all 300ms ease-in-out !important;
      }
      
      /* Icon animation */
      .theme-toggle i {
        display: inline-block;
        transition: transform 300ms ease-in-out;
      }
      
      .theme-toggle:hover i {
        transform: rotate(20deg) scale(1.1);
      }
      
      /* Prevent transition on initial page load */
      :root:not([data-theme]) * {
        transition: none !important;
      }
    `;
    document.head.appendChild(style);
  }

  /**
   * Observe and apply theme to dynamically added content
   */
  observeDynamicContent() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          // Apply current theme to new elements
          const currentTheme = document.documentElement.getAttribute('data-theme');
          if (currentTheme) {
            // Trigger re-flow if needed
            void document.documentElement.offsetHeight;
          }
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: false
    });
  }

  /**
   * Get current theme
   */
  getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
  }

  /**
   * Set theme programmatically
   */
  setTheme(theme) {
    if (['light', 'dark'].includes(theme)) {
      this.applyTheme(theme);
      this.updateThemeUI(theme);
    } else {
      console.error(`Invalid theme: ${theme}`);
    }
  }

  /**
   * Reset to system preference
   */
  resetToSystemPreference() {
    localStorage.removeItem(this.THEME_KEY);
    this.loadTheme();
  }

  /**
   * Export theme settings
   */
  exportSettings() {
    return {
      theme: this.getCurrentTheme(),
      savedAt: new Date().toISOString()
    };
  }
}

/**
 * Initialize theme manager when DOM is ready
 */
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
  });
} else {
  window.themeManager = new ThemeManager();
}

/**
 * Expose theme API globally
 */
window.toggleTheme = () => {
  if (window.themeManager) {
    window.themeManager.toggleTheme();
  }
};

window.setTheme = (theme) => {
  if (window.themeManager) {
    window.themeManager.setTheme(theme);
  }
};

window.getCurrentTheme = () => {
  if (window.themeManager) {
    return window.themeManager.getCurrentTheme();
  }
  return 'light';
};

/**
 * Listen for theme changes
 */
window.addEventListener('themechange', (e) => {
  console.log(`Theme changed to: ${e.detail.theme}`);
  // Trigger any custom theme change handlers here
  document.body.classList.remove('theme-changing');
});
