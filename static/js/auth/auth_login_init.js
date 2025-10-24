/**
 * Login page initialization
 *
 * Handles login form submission via AJAX and integrates with
 * the shared auth-forms module for message display and password toggling.
 */

import { showMessage } from '../utils/util_auth_forms.js';
import { API_ENDPOINTS } from '../utils/util_config.js';

// Handle form submission via AJAX
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('login-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const submitButton = this.querySelector('button[type="submit"]');
        const originalButtonText = submitButton.textContent;

        // Disable button and show loading state
        submitButton.disabled = true;
        submitButton.textContent = 'LOGGING IN...';

        try {
            const response = await fetch(API_ENDPOINTS.auth.login, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // Always try to parse JSON response
            const data = await response.json();

            // Check if request was successful based on HTTP status code
            if (response.ok) {
                showMessage(data.detail, false);
                // Redirect after a short delay
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                // Handle error response
                showMessage(data.detail, true);
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            }
        } catch (error) {
            console.error('Login exception:', error);
            showMessage('An error occurred. Please try again.', true);
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
        }
    });
});
