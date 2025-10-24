/**
 * Unified Message Handling System
 *
 * Single source of truth for displaying and dismissing messages.
 * Design: Only ONE message is shown at a time for clarity.
 *
 * API:
 * - showMessage(message, isError) - Display a message
 * - dismissMessage() - Dismiss the current message
 */

let messageTimeout = null;
let currentMessage = null;

/**
 * Display a message to the user
 *
 * Only ONE message is shown at a time. If a message already exists,
 * it will be instantly replaced by the new one.
 *
 * @param {string} message - The message text to display
 * @param {boolean} isError - Whether this is an error (true) or success (false)
 */
export function showMessage(message, isError = false) {
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
    let container = document.querySelector('.messages');
    if (!container) {
        container = document.createElement('div');
        container.className = 'messages';
        document.body.prepend(container);
    }

    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isError ? 'error' : 'success'}`;
    messageDiv.textContent = message;

    // Add close button
    const closeButton = document.createElement('button');
    closeButton.type = 'button';
    closeButton.className = 'message-close';
    closeButton.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
    `;
    closeButton.addEventListener('click', (e) => {
        e.preventDefault();
        dismissMessage();
    });
    messageDiv.appendChild(closeButton);

    // Add to DOM and track
    container.appendChild(messageDiv);
    currentMessage = messageDiv;

    // Auto-dismiss after 5 seconds
    messageTimeout = setTimeout(() => {
        dismissMessage();
    }, 5000);
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

    // Add fadeOut animation
    currentMessage.style.animation = 'fadeOut 0.3s ease-out forwards';

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
    }, 300);
}

/**
 * Initialize message handlers for server-rendered Django messages
 * Call this once on page load from base.js
 */
export function initMessages() {
    document.addEventListener('DOMContentLoaded', function() {
        // Auto-dismiss server-rendered messages
        const messages = document.querySelectorAll('.message');
        messages.forEach(message => {
            // Skip hidden containers
            const container = message.closest('.messages');
            if (container && container.style.display === 'none') {
                return;
            }

            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                message.style.animation = 'fadeOut 0.3s ease-out forwards';
                setTimeout(() => {
                    const parent = message.parentElement;
                    message.remove();
                    if (parent && parent.children.length === 0) {
                        parent.remove();
                    }
                }, 300);
            }, 5000);
        });

        // Handle all close button clicks (event delegation)
        document.addEventListener('click', (e) => {
            const closeButton = e.target.closest('.message-close, .ajax-message-close');
            if (closeButton) {
                e.preventDefault();
                const message = closeButton.closest('.message');
                if (message) {
                    message.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => {
                        const parent = message.parentElement;
                        message.remove();
                        if (parent && parent.children.length === 0) {
                            parent.remove();
                        }
                    }, 300);
                }
            }
        });
    });
}
