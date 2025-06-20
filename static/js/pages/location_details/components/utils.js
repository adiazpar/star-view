// Utility Functions Component
window.LocationDetailsUtils = (function() {
    'use strict';
    
    // Format date for display
    function formatDate(dateString) {
        if (!dateString) return 'Unknown date';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        } catch (error) {
            return 'Invalid date';
        }
    }
    
    // Simple event bus for component communication
    function createEventBus() {
        const events = {};
        
        return {
            on: function(event, callback) {
                if (!events[event]) {
                    events[event] = [];
                }
                events[event].push(callback);
            },
            
            emit: function(event, data) {
                if (events[event]) {
                    events[event].forEach(callback => callback(data));
                }
            },
            
            off: function(event, callback) {
                if (events[event]) {
                    events[event] = events[event].filter(cb => cb !== callback);
                }
            }
        };
    }
    
    // Show a message to the user
    function showMessage(message, type) {
        const messageEl = document.createElement('div');
        messageEl.className = `gallery-message ${type}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10000;
            padding: var(--space-sm) var(--space-md); border-radius: var(--radius-sm);
            color: white; font-size: var(--font-size-sm); max-width: 300px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            background: ${type === 'success' ? 'var(--success)' : 'var(--negate)'};
        `;
        
        document.body.appendChild(messageEl);
        
        setTimeout(() => {
            messageEl.remove();
        }, 3000);
    }
    
    // Debounce function for performance optimization
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Throttle function for performance optimization
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Get configuration from global object
    function getConfig() {
        return window.locationDetailsConfig || {};
    }
    
    // Get CSRF token
    function getCsrfToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Validate required configuration
    function validateConfig(config) {
        const required = ['locationId', 'isAuthenticated', 'currentUsername'];
        const missing = required.filter(key => config[key] === undefined);
        
        if (missing.length > 0) {
            console.error('Missing required configuration:', missing);
            return false;
        }
        
        return true;
    }
    
    // Create a safe API request function
    function apiRequest(url, options = {}) {
        const defaultOptions = {
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                ...options.headers
            }
        };
        
        return fetch(url, { ...defaultOptions, ...options })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(error => {
                        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
                    });
                }
                return response.json();
            });
    }
    
    // Generate unique ID
    function generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    }
    
    // Safely parse JSON
    function safeJsonParse(str, fallback = null) {
        try {
            return JSON.parse(str);
        } catch (e) {
            console.warn('Failed to parse JSON:', str);
            return fallback;
        }
    }
    
    // Check if element is visible in viewport
    function isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API
    return {
        formatDate: formatDate,
        createEventBus: createEventBus,
        showMessage: showMessage,
        debounce: debounce,
        throttle: throttle,
        getConfig: getConfig,
        getCsrfToken: getCsrfToken,
        validateConfig: validateConfig,
        apiRequest: apiRequest,
        generateId: generateId,
        safeJsonParse: safeJsonParse,
        isElementVisible: isElementVisible,
        escapeHtml: escapeHtml
    };
})();