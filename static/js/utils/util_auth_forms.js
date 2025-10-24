/**
 * Shared Authentication Form Utilities
 *
 * Common functionality for authentication pages (login, register, password reset).
 *
 * Functions:
 * - togglePassword(inputId): Toggle password visibility
 * - showMessage, dismissMessage: Re-exported from messages.js
 */

// Re-export message functions from single source of truth
export { showMessage, dismissMessage } from './util_messages.js';

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

// Make togglePassword available globally for inline onclick handlers
window.togglePassword = togglePassword;
