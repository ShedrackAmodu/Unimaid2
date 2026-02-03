/**
 * ============================================================================
 * PROFESSIONAL JAVASCRIPT UTILITIES - Ramat Library
 * ============================================================================
 * A comprehensive utility library for professional, consistent interactions
 * across all templates with accessibility and responsiveness in mind.
 */

/**
 * ============================================================================
 * 1. UTILITY OBJECT - Global namespace to prevent conflicts
 * ============================================================================
 */

const RamatLibrary = {
  // Configuration
  config: {
    transitionSpeed: 300,
    debounceDelay: 250,
    mobileBreakpoint: 768,
  },

  // Version
  version: '2.1.0',

  // Initialize all utilities
  init() {
    console.log(`🚀 Ramat Library v${this.version} initializing...`);
    
    this.DOM.init();
    this.Events.init();
    this.Accessibility.init();
    this.Performance.init();
    
    console.log('✅ Ramat Library initialized successfully');
  },

  /**
   * ============================================================================
   * 2. DOM MANIPULATION UTILITIES
   * ============================================================================
   */

  DOM: {
    init() {
      this.setupDOMObserver();
      this.enhanceInteractiveElements();
    },

    /**
     * Safe element selection with error handling
     */
    select(selector) {
      if (!selector) {
        console.warn('Select: No selector provided');
        return null;
      }
      try {
        return document.querySelector(selector);
      } catch (e) {
        console.error(`Select: Invalid selector "${selector}"`, e);
        return null;
      }
    },

    /**
     * Safe multi-element selection
     */
    selectAll(selector) {
      if (!selector) return [];
      try {
        return Array.from(document.querySelectorAll(selector));
      } catch (e) {
        console.error(`SelectAll: Invalid selector "${selector}"`, e);
        return [];
      }
    },

    /**
     * Add class with validation
     */
    addClass(element, className) {
      if (!element || !className) return;
      element.classList.add(className);
    },

    /**
     * Remove class with validation
     */
    removeClass(element, className) {
      if (!element || !className) return;
      element.classList.remove(className);
    },

    /**
     * Toggle class
     */
    toggleClass(element, className) {
      if (!element || !className) return;
      element.classList.toggle(className);
    },

    /**
     * Check if element has class
     */
    hasClass(element, className) {
      if (!element || !className) return false;
      return element.classList.contains(className);
    },

    /**
     * Add multiple classes
     */
    addClasses(element, classes) {
      if (!element || !Array.isArray(classes)) return;
      classes.forEach(cls => this.addClass(element, cls));
    },

    /**
     * Remove multiple classes
     */
    removeClasses(element, classes) {
      if (!element || !Array.isArray(classes)) return;
      classes.forEach(cls => this.removeClass(element, cls));
    },

    /**
     * Set attributes with validation
     */
    setAttribute(element, attr, value) {
      if (!element) return;
      element.setAttribute(attr, value);
    },

    /**
     * Get attributes with validation
     */
    getAttribute(element, attr) {
      if (!element) return null;
      return element.getAttribute(attr);
    },

    /**
     * Safe text content update
     */
    setText(element, text) {
      if (!element) return;
      element.textContent = String(text);
    },

    /**
     * Safe HTML content update (use with caution - sanitize input)
     */
    setHTML(element, html) {
      if (!element) return;
      element.innerHTML = String(html);
    },

    /**
     * Observe DOM changes
     */
    setupDOMObserver() {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList') {
            // Re-initialize dynamic content
            this.enhanceInteractiveElements();
          }
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });
    },

    /**
     * Enhance all interactive elements
     */
    enhanceInteractiveElements() {
      // Add focus indicators
      this.selectAll('[role="button"], .btn, a').forEach(el => {
        el.style.outline = el.style.outline || 'none';
      });
    },
  },

  /**
   * ============================================================================
   * 3. EVENT HANDLING UTILITIES
   * ============================================================================
   */

  Events: {
    init() {
      this.setupWindowEvents();
      this.setupKeyboardShortcuts();
    },

    /**
     * Add event listener with error handling
     */
    on(element, event, callback, options = {}) {
      if (!element || !event || !callback) {
        console.warn('Event.on: Invalid parameters');
        return;
      }
      try {
        element.addEventListener(event, callback, options);
      } catch (e) {
        console.error(`Event.on: Error adding listener for "${event}"`, e);
      }
    },

    /**
     * Remove event listener
     */
    off(element, event, callback) {
      if (!element || !event) return;
      try {
        element.removeEventListener(event, callback);
      } catch (e) {
        console.error(`Event.off: Error removing listener for "${event}"`, e);
      }
    },

    /**
     * One-time event listener
     */
    once(element, event, callback) {
      if (!element || !event) return;
      const handler = (...args) => {
        callback(...args);
        this.off(element, event, handler);
      };
      this.on(element, event, handler);
    },

    /**
     * Emit custom events
     */
    emit(eventName, detail = {}) {
      const event = new CustomEvent(eventName, { detail });
      window.dispatchEvent(event);
    },

    /**
     * Listen for custom events
     */
    onCustom(eventName, callback) {
      window.addEventListener(eventName, (e) => {
        callback(e.detail);
      });
    },

    /**
     * Debounce function execution
     */
    debounce(func, wait = RamatLibrary.config.debounceDelay) {
      let timeout;
      return function executedFunction(...args) {
        const later = () => {
          clearTimeout(timeout);
          func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
      };
    },

    /**
     * Throttle function execution
     */
    throttle(func, limit = RamatLibrary.config.debounceDelay) {
      let inThrottle;
      return function(...args) {
        if (!inThrottle) {
          func.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    },

    /**
     * Setup window-level events
     */
    setupWindowEvents() {
      // Handle resize events with debounce
      window.addEventListener('resize', this.debounce(() => {
        RamatLibrary.emit('window-resized', {
          width: window.innerWidth,
          height: window.innerHeight,
          isMobile: window.innerWidth < RamatLibrary.config.mobileBreakpoint,
        });
      }, 250));

      // Handle scroll events with throttle
      window.addEventListener('scroll', this.throttle(() => {
        RamatLibrary.emit('window-scrolled', {
          scrollY: window.scrollY,
          scrollX: window.scrollX,
        });
      }, 100));

      // Handle visibility changes
      document.addEventListener('visibilitychange', () => {
        const isVisible = !document.hidden;
        RamatLibrary.emit('visibility-changed', { visible: isVisible });
        console.log(isVisible ? '👁️ Page visible' : '👁️ Page hidden');
      });

      // Online/Offline detection
      window.addEventListener('online', () => {
        RamatLibrary.emit('connection-changed', { online: true });
        console.log('🌐 Connection restored');
      });

      window.addEventListener('offline', () => {
        RamatLibrary.emit('connection-changed', { online: false });
        console.log('🌐 Connection lost');
      });
    },

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
      document.addEventListener('keydown', (e) => {
        // Ctrl/Cmd + T: Toggle theme
        if ((e.ctrlKey || e.metaKey) && e.key === 't') {
          e.preventDefault();
          RamatLibrary.Theme.toggle();
        }

        // Escape: Close dropdowns and modals
        if (e.key === 'Escape') {
          document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            if (toggle) {
              bootstrap.Dropdown.getInstance(toggle)?.hide();
            }
          });
        }

        // Ctrl/Cmd + /: Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === '/') {
          e.preventDefault();
          const search = document.querySelector('[role="search"]');
          if (search) search.focus();
        }
      });
    },
  },

  /**
   * ============================================================================
   * 4. ANIMATION & TRANSITION UTILITIES
   * ============================================================================
   */

  Animation: {
    /**
     * Fade in element
     */
    fadeIn(element, duration = RamatLibrary.config.transitionSpeed) {
      if (!element) return;
      element.style.opacity = '0';
      element.style.display = 'block';
      element.style.transition = `opacity ${duration}ms ease-in-out`;

      // Trigger reflow
      element.offsetHeight;

      element.style.opacity = '1';

      setTimeout(() => {
        element.style.transition = '';
      }, duration);
    },

    /**
     * Fade out element
     */
    fadeOut(element, duration = RamatLibrary.config.transitionSpeed) {
      if (!element) return;
      element.style.opacity = '1';
      element.style.transition = `opacity ${duration}ms ease-in-out`;
      element.style.opacity = '0';

      setTimeout(() => {
        element.style.display = 'none';
        element.style.transition = '';
      }, duration);
    },

    /**
     * Slide down element
     */
    slideDown(element, duration = RamatLibrary.config.transitionSpeed) {
      if (!element) return;
      element.style.maxHeight = '0px';
      element.style.overflow = 'hidden';
      element.style.transition = `max-height ${duration}ms ease-in-out`;

      // Trigger reflow
      element.offsetHeight;

      element.style.maxHeight = element.scrollHeight + 'px';

      setTimeout(() => {
        element.style.transition = '';
        element.style.maxHeight = 'none';
      }, duration);
    },

    /**
     * Slide up element
     */
    slideUp(element, duration = RamatLibrary.config.transitionSpeed) {
      if (!element) return;
      element.style.maxHeight = element.scrollHeight + 'px';
      element.style.overflow = 'hidden';
      element.style.transition = `max-height ${duration}ms ease-in-out`;

      // Trigger reflow
      element.offsetHeight;

      element.style.maxHeight = '0px';

      setTimeout(() => {
        element.style.display = 'none';
        element.style.transition = '';
        element.style.maxHeight = 'none';
      }, duration);
    },

    /**
     * Bounce animation
     */
    bounce(element) {
      if (!element) return;
      RamatLibrary.DOM.addClass(element, 'animate__animated');
      RamatLibrary.DOM.addClass(element, 'animate__bounce');

      setTimeout(() => {
        RamatLibrary.DOM.removeClass(element, 'animate__animated');
        RamatLibrary.DOM.removeClass(element, 'animate__bounce');
      }, 1000);
    },

    /**
     * Pulse animation
     */
    pulse(element) {
      if (!element) return;
      RamatLibrary.DOM.addClass(element, 'animate__animated');
      RamatLibrary.DOM.addClass(element, 'animate__pulse');

      setTimeout(() => {
        RamatLibrary.DOM.removeClass(element, 'animate__animated');
        RamatLibrary.DOM.removeClass(element, 'animate__pulse');
      }, 1000);
    },
  },

  /**
   * ============================================================================
   * 5. THEME MANAGEMENT
   * ============================================================================
   */

  Theme: {
    STORAGE_KEY: 'ramat-library-theme',

    /**
     * Get current theme
     */
    getCurrent() {
      return document.documentElement.getAttribute('data-theme') || 'light';
    },

    /**
     * Get saved theme
     */
    getSaved() {
      return localStorage.getItem(this.STORAGE_KEY) || null;
    },

    /**
     * Apply theme
     */
    apply(theme) {
      if (!['light', 'dark'].includes(theme)) {
        console.warn(`Invalid theme: ${theme}`);
        return;
      }

      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem(this.STORAGE_KEY, theme);

      // Update icon
      const icon = document.querySelector('#themeToggle i');
      if (icon) {
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
      }

      RamatLibrary.emit('theme-changed', { theme });
      console.log(`🎨 Theme applied: ${theme}`);
    },

    /**
     * Toggle theme
     */
    toggle() {
      const current = this.getCurrent();
      const newTheme = current === 'light' ? 'dark' : 'light';
      this.apply(newTheme);
    },

    /**
     * Initialize theme based on preference
     */
    init() {
      let themeToApply = this.getSaved();

      if (!themeToApply) {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        themeToApply = prefersDark ? 'dark' : 'light';
      }

      this.apply(themeToApply);
    },
  },

  /**
   * ============================================================================
   * 6. ACCESSIBILITY UTILITIES
   * ============================================================================
   */

  Accessibility: {
    init() {
      this.enhanceAnnouncements();
      this.improveKeyboardNavigation();
      this.setupFocusManagement();
    },

    /**
     * Announce text to screen readers
     */
    announce(message, priority = 'polite') {
      const element = document.createElement('div');
      element.setAttribute('role', 'status');
      element.setAttribute('aria-live', priority);
      element.setAttribute('aria-atomic', 'true');
      element.style.position = 'absolute';
      element.style.left = '-10000px';
      element.textContent = message;

      document.body.appendChild(element);

      setTimeout(() => {
        element.remove();
      }, 5000);
    },

    /**
     * Enhance announcements
     */
    enhanceAnnouncements() {
      // Announce page title changes
      const observer = new MutationObserver(() => {
        const title = document.title;
        this.announce(`Page: ${title}`);
      });

      observer.observe(document.head, { childList: true });
    },

    /**
     * Improve keyboard navigation
     */
    improveKeyboardNavigation() {
      // Add tabindex to interactive elements without it
      document.querySelectorAll('.card, .btn').forEach(el => {
        if (!el.hasAttribute('tabindex')) {
          el.setAttribute('tabindex', '0');
        }
      });
    },

    /**
     * Setup focus management
     */
    setupFocusManagement() {
      document.addEventListener('focusin', (e) => {
        if (e.target.classList.contains('btn') || e.target.classList.contains('nav-link')) {
          RamatLibrary.emit('interactive-focused', { element: e.target });
        }
      });
    },

    /**
     * Check if reduced motion is preferred
     */
    prefersReducedMotion() {
      return window.matchMedia('(prefers-motion-reduce)').matches;
    },

    /**
     * Skip to main content
     */
    addSkipLink() {
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.className = 'skip-link';
      skipLink.textContent = 'Skip to main content';
      skipLink.style.cssText = `
        position: absolute;
        top: -40px;
        left: 0;
        background: var(--primary-blue);
        color: white;
        padding: 8px;
        z-index: 100;
      `;

      skipLink.addEventListener('focus', () => {
        skipLink.style.top = '0';
      });

      skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-40px';
      });

      document.body.insertBefore(skipLink, document.body.firstChild);
    },
  },

  /**
   * ============================================================================
   * 7. NOTIFICATION SYSTEM
   * ============================================================================
   */

  Notifications: {
    /**
     * Show toast notification
     */
    toast(message, type = 'info', duration = 3000) {
      const toast = document.createElement('div');
      toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
      toast.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        animation: slideInDown 0.3s ease;
      `;

      const icons = {
        success: 'check-circle-fill',
        danger: 'exclamation-circle-fill',
        warning: 'exclamation-triangle-fill',
        info: 'info-circle-fill',
      };

      toast.innerHTML = `
        <div class="d-flex align-items-center">
          <i class="bi bi-${icons[type] || icons.info} fs-4 me-3"></i>
          <div class="flex-grow-1">${message}</div>
          <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
      `;

      document.body.appendChild(toast);

      setTimeout(() => {
        if (toast.parentNode) {
          RamatLibrary.Animation.fadeOut(toast, 300);
          setTimeout(() => toast.remove(), 300);
        }
      }, duration);
    },

    /**
     * Show alert dialog
     */
    alert(message, type = 'info') {
      this.toast(message, type, 5000);
      RamatLibrary.Accessibility.announce(message);
    },

    /**
     * Show confirm dialog
     */
    confirm(message, onConfirm, onCancel) {
      // This would typically use a modal, but simple implementation:
      if (window.confirm(message)) {
        onConfirm?.();
      } else {
        onCancel?.();
      }
    },
  },

  /**
   * ============================================================================
   * 8. RESPONSIVE UTILITIES
   * ============================================================================
   */

  Responsive: {
    /**
     * Check if device is mobile
     */
    isMobile() {
      return window.innerWidth < RamatLibrary.config.mobileBreakpoint;
    },

    /**
     * Get current breakpoint
     */
    getBreakpoint() {
      const width = window.innerWidth;
      if (width < 576) return 'xs';
      if (width < 768) return 'sm';
      if (width < 992) return 'md';
      if (width < 1200) return 'lg';
      if (width < 1400) return 'xl';
      return '2xl';
    },

    /**
     * Get viewport dimensions
     */
    getViewport() {
      return {
        width: window.innerWidth,
        height: window.innerHeight,
        orientation: window.innerHeight > window.innerWidth ? 'portrait' : 'landscape',
      };
    },

    /**
     * Watch for breakpoint changes
     */
    onBreakpointChange(callback) {
      let lastBreakpoint = this.getBreakpoint();

      RamatLibrary.onCustom('window-resized', () => {
        const newBreakpoint = this.getBreakpoint();
        if (newBreakpoint !== lastBreakpoint) {
          lastBreakpoint = newBreakpoint;
          callback(newBreakpoint);
        }
      });
    },
  },

  /**
   * ============================================================================
   * 9. PERFORMANCE UTILITIES
   * ============================================================================
   */

  Performance: {
    init() {
      this.monitorPerformance();
      this.optimizeImages();
      this.lazyLoadContent();
    },

    /**
     * Monitor page performance
     */
    monitorPerformance() {
      if (window.PerformanceObserver) {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 3000) {
              console.warn(`⚠️ Slow operation: ${entry.name} (${entry.duration.toFixed(2)}ms)`);
            }
          }
        });

        observer.observe({ entryTypes: ['measure', 'navigation'] });
      }
    },

    /**
     * Optimize images
     */
    optimizeImages() {
      document.querySelectorAll('img').forEach(img => {
        // Lazy load if not already set
        if (!img.hasAttribute('loading')) {
          img.setAttribute('loading', 'lazy');
        }

        // Set decoding
        if (!img.hasAttribute('decoding')) {
          img.setAttribute('decoding', 'async');
        }
      });
    },

    /**
     * Lazy load content
     */
    lazyLoadContent() {
      if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const element = entry.target;
              
              // Load data-src if present
              if (element.hasAttribute('data-src')) {
                element.src = element.getAttribute('data-src');
              }

              observer.unobserve(element);
            }
          });
        });

        document.querySelectorAll('[data-src]').forEach(el => {
          observer.observe(el);
        });
      }
    },
  },

  /**
   * ============================================================================
   * 10. STORAGE UTILITIES
   * ============================================================================
   */

  Storage: {
    /**
     * Safely store data
     */
    set(key, value) {
      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch (e) {
        console.error('Storage: Failed to set item', e);
        return false;
      }
    },

    /**
     * Safely retrieve data
     */
    get(key, defaultValue = null) {
      try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
      } catch (e) {
        console.error('Storage: Failed to get item', e);
        return defaultValue;
      }
    },

    /**
     * Remove item
     */
    remove(key) {
      try {
        localStorage.removeItem(key);
        return true;
      } catch (e) {
        console.error('Storage: Failed to remove item', e);
        return false;
      }
    },

    /**
     * Clear all
     */
    clear() {
      try {
        localStorage.clear();
        return true;
      } catch (e) {
        console.error('Storage: Failed to clear', e);
        return false;
      }
    },
  },
};

/**
 * ============================================================================
 * INITIALIZATION
 * ============================================================================
 */

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    RamatLibrary.init();
  });
} else {
  RamatLibrary.init();
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = RamatLibrary;
}
