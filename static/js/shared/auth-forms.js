/**
 * Shared Authentication Form Utilities
 *
 * This module contains common functionality used across authentication pages
 * (login, register, password reset) to avoid code duplication.
 *
 * Exported Functions:
 * - togglePassword(inputId): Toggle password visibility
 * - showMessage(message, isError): Display success/error messages
 * - hideMessage(): Hide message display
 * - initMessageHandlers(): Initialize message close button handlers
 */

// Store timeout ID so we can clear it if needed
let messageTimeout = null;

/**
 * Toggle password visibility for a password input field
 * @param {string} inputId - The ID of the password input element
 */
export function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';

    // Update icon
    const button = input.nextElementSibling;
    const icon = button.querySelector('svg');
    if (input.type === 'text') {
        icon.innerHTML = `
            <line x1="3" y1="3" x2="21" y2="21"></line>
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        `;
    } else {
        icon.innerHTML = `
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        `;
    }
}

/**
 * Display a success or error message to the user
 * @param {string} message - The message text to display
 * @param {boolean} isError - Whether this is an error (true) or success (false) message
 */
export function showMessage(message, isError = false) {
    const container = document.getElementById('messages-container');
    const messageContent = document.getElementById('message-content');
    const messageText = document.getElementById('message-text');

    // Safety check: if elements don't exist, log error
    if (!container || !messageContent || !messageText) {
        console.error('Message elements not found in DOM');
        return;
    }

    // Clear any existing timeout
    if (messageTimeout) {
        clearTimeout(messageTimeout);
    }

    messageText.textContent = message;
    messageContent.className = isError ? 'message error' : 'message success';
    container.style.display = 'block';

    // Auto-dismiss after 5 seconds
    messageTimeout = setTimeout(() => {
        hideMessage();
    }, 5000);
}

/**
 * Hide the message display
 */
export function hideMessage() {
    const container = document.getElementById('messages-container');
    if (container) {
        container.style.display = 'none';
    }

    // Clear the timeout
    if (messageTimeout) {
        clearTimeout(messageTimeout);
        messageTimeout = null;
    }
}

/**
 * Initialize message close button handlers
 * Call this on DOMContentLoaded to set up the close button
 */
export function initMessageHandlers() {
    const closeBtn = document.getElementById('message-close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();  // Prevent base.html event listener from firing
            hideMessage();
        });
    }
}

// Make togglePassword available globally for inline onclick handlers
window.togglePassword = togglePassword;
