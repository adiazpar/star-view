/**
 * Authentication API Service
 *
 * All API calls related to user authentication and account management.
 * Each function returns a Promise that resolves to the API response.
 */

import api from './api';

export const authApi = {
  /**
   * Check authentication status
   * @returns {Promise} - { authenticated: boolean, user: Object|null }
   */
  checkStatus: () => {
    return api.get('/auth/status/');
  },

  /**
   * Register a new user
   * @param {Object} data - Registration data
   * @param {string} data.username - Username
   * @param {string} data.email - Email address
   * @param {string} data.first_name - First name
   * @param {string} data.last_name - Last name
   * @param {string} data.password1 - Password
   * @param {string} data.password2 - Password confirmation
   * @returns {Promise} - { detail: string, redirect_url: string }
   */
  register: (data) => {
    return api.post('/auth/register/', data);
  },

  /**
   * Login user
   * @param {Object} credentials - Login credentials
   * @param {string} credentials.username - Username or email
   * @param {string} credentials.password - Password
   * @param {string} [credentials.next] - Optional redirect URL after login
   * @returns {Promise} - { detail: string, redirect_url: string }
   */
  login: (credentials) => {
    return api.post('/auth/login/', credentials);
  },

  /**
   * Logout current user
   * @returns {Promise} - { detail: string, redirect_url: string }
   */
  logout: () => {
    return api.post('/auth/logout/');
  },

  /**
   * Request password reset email
   * @param {string} email - User's email address
   * @returns {Promise}
   */
  requestPasswordReset: (email) => {
    return api.post('/password-reset/', { email });
  },
};

export default authApi;
