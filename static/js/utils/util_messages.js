/**
 * Unified Message Handling System
 *
 * Single source of truth for displaying and dismissing messages.
 * Design: Only ONE message is shown at a time for clarity.
 *
 * API:
 * - showMessage(message, type) - Display a message
 *   - type: 'success' (default), 'error', 'warning', or 'info'
 * - dismissMessage() - Dismiss the current message
 * - initMessages() - Initialize for Django server-rendered messages
 */

// ============================================================================
// CSS CLASSES - Update these if you rename CSS classes
// ============================================================================
const CSS_CLASSES = {
    MESSAGE_CONTAINER: 'message-container',
    MESSAGE: 'message',
    MESSAGE_TEXT: 'message-text',
    MESSAGE_CLOSE: 'message-close',
    FADE_OUT: 'fade-out',
    SUCCESS: 'success',
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
};

const TIMING = {
    AUTO_DISMISS: 5000,
    FADE_OUT_DURATION: 300
};

let messageTimeout = null;
let currentMessage = null;

/**
 * Display a message to the user
 *
 * Only ONE message is shown at a time. If a message already exists,
 * it will be instantly replaced by the new one.
 *
 * @param {string} message - The message text to display
 * @param {string} type - Message type: 'success' (default), 'error', 'warning', or 'info'
 */
export function showMessage(message, type = 'success') {
    // Clear existing timeout
    if (messageTimeout) {
        clearTimeout(messageTimeout);
        messageTimeout = null;
    }

    // Remove current message instantly (no animation)
    if (currentMessage && currentMessage.parentElement) {
        currentMessage.remove();
        currentMessage = null;
    }

    // Find or create messages container
    let container = document.querySelector(`.${CSS_CLASSES.MESSAGE_CONTAINER}`);
    if (!container) {
        container = document.createElement('div');
        container.className = CSS_CLASSES.MESSAGE_CONTAINER;
        document.body.prepend(container);
    }

    // Validate type and set default
    const validTypes = [CSS_CLASSES.SUCCESS, CSS_CLASSES.ERROR, CSS_CLASSES.WARNING, CSS_CLASSES.INFO];
    const messageClass = validTypes.includes(type) ? type : CSS_CLASSES.SUCCESS;

    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `${CSS_CLASSES.MESSAGE} ${messageClass}`;

    // Create message text wrapper
    const messageText = document.createElement('div');
    messageText.className = CSS_CLASSES.MESSAGE_TEXT;
    messageText.textContent = message;
    messageDiv.appendChild(messageText);

    // Add close button
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = CSS_CLASSES.MESSAGE_CLOSE;
    closeButton.innerHTML = '<i class="fas fa-xmark"></i>';
    closeButton.addEventListener('click', (e) => {
        e.preventDefault();
        dismissMessage();
    });
    messageDiv.appendChild(closeButton);

    // Add to DOM and track
    container.appendChild(messageDiv);
    currentMessage = messageDiv;

    // Auto-dismiss after configured time
    messageTimeout = setTimeout(() => {
        dismissMessage();
    }, TIMING.AUTO_DISMISS);
    
}

/**
 * Dismiss the currently displayed message
 */
export function dismissMessage() {
    if (messageTimeout) {
        clearTimeout(messageTimeout);
        messageTimeout = null;
    }

    if (!currentMessage) return;

    // Add fadeOut class
    currentMessage.classList.add(CSS_CLASSES.FADE_OUT);

    // Remove from DOM after animation
    setTimeout(() => {
        if (currentMessage && currentMessage.parentElement) {
            const container = currentMessage.parentElement;
            currentMessage.remove();

            // Clean up empty container
            if (container && container.children.length === 0) {
                container.remove();
            }
        }
        currentMessage = null;
    }, TIMING.FADE_OUT_DURATION);
}

/**
 * Initialize message handlers for server-rendered Django messages
 * Call this once on page load from base.js
 */
export function initMessages() {
    document.addEventListener('DOMContentLoaded', function() {
        // Auto-dismiss server-rendered messages
        const messages = document.querySelectorAll(`.${CSS_CLASSES.MESSAGE}`);
        messages.forEach(message => {
            // Skip hidden containers
            const container = message.closest(`.${CSS_CLASSES.MESSAGE_CONTAINER}`);
            if (container && container.style.display === 'none') {
                return;
            }

            // Auto-dismiss after configured time
            setTimeout(() => {
                message.classList.add(CSS_CLASSES.FADE_OUT);
                setTimeout(() => {
                    const parent = message.parentElement;
                    message.remove();
                    if (parent && parent.children.length === 0) {
                        parent.remove();
                    }
                }, TIMING.FADE_OUT_DURATION);
            }, TIMING.AUTO_DISMISS);
        });

        // Handle all close button clicks (event delegation)
        document.addEventListener('click', (e) => {
            const closeButton = e.target.closest(`.${CSS_CLASSES.MESSAGE_CLOSE}`);
            if (closeButton) {
                e.preventDefault();
                const message = closeButton.closest(`.${CSS_CLASSES.MESSAGE}`);
                if (message) {
                    message.classList.add(CSS_CLASSES.FADE_OUT);
                    setTimeout(() => {
                        const parent = message.parentElement;
                        message.remove();
                        if (parent && parent.children.length === 0) {
                            parent.remove();
                        }
                    }, TIMING.FADE_OUT_DURATION);
                }
            }
        });
    });
}
