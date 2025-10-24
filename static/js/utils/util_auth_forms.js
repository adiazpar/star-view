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

    // Update icon (Font Awesome)
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    if (input.type === 'text') {
        // Password is visible, show eye-slash icon
        icon.className = 'fas fa-eye-slash eye-icon';
    } else {
        // Password is hidden, show regular eye icon
        icon.className = 'fas fa-eye eye-icon';
    }
}

// Make togglePassword available globally for inline onclick handlers
window.togglePassword = togglePassword;
