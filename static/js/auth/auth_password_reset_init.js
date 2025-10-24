/**
 * Password reset confirmation page initialization
 *
 * Handles password visibility toggling for the password reset form.
 * Uses the shared auth-forms module for consistent password toggle behavior.
 */

import { togglePassword } from '../../utils/util_auth_forms.js';

// Make togglePassword available globally for inline onclick handlers
// (This maintains backward compatibility while we migrate away from inline handlers)
window.togglePassword = togglePassword;
