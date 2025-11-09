/**
 * Profile API Service
 *
 * All API calls related to user profile management.
 * Each function returns a Promise that resolves to the API response.
 */

import api from './api';

export const profileApi = {
  /**
   * Upload profile picture
   * @param {File} file - Image file to upload
   * @returns {Promise} - { detail: string, image_url: string }
   */
  uploadProfilePicture: (file) => {
    const formData = new FormData();
    formData.append('profile_picture', file);

    return api.post('/profile/upload-picture/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  /**
   * Remove profile picture (reset to default)
   * @returns {Promise} - { detail: string, default_image_url: string }
   */
  removeProfilePicture: () => {
    return api.delete('/profile/remove-picture/');
  },

  /**
   * Update user's first and last name
   * @param {Object} data - Name data
   * @param {string} data.first_name - First name
   * @param {string} data.last_name - Last name
   * @returns {Promise} - { detail: string, first_name: string, last_name: string }
   */
  updateName: (data) => {
    return api.patch('/profile/update-name/', data);
  },

  /**
   * Update user's username
   * @param {Object} data - Username data
   * @param {string} data.new_username - New username
   * @returns {Promise} - { detail: string, username: string }
   */
  updateUsername: (data) => {
    return api.patch('/profile/update-username/', data);
  },

  /**
   * Update user's email address
   * @param {Object} data - Email data
   * @param {string} data.new_email - New email address
   * @returns {Promise} - { detail: string, new_email: string }
   */
  updateEmail: (data) => {
    return api.patch('/profile/update-email/', data);
  },

  /**
   * Update user's password
   * @param {Object} data - Password data
   * @param {string} data.current_password - Current password
   * @param {string} data.new_password - New password
   * @returns {Promise} - { detail: string }
   */
  updatePassword: (data) => {
    return api.patch('/profile/update-password/', data);
  },

  /**
   * Get user's favorite locations
   * @returns {Promise} - Array of favorite locations
   */
  getFavorites: () => {
    return api.get('/favorite-locations/');
  },

  /**
   * Remove a favorite location
   * @param {number} id - Favorite location ID
   * @returns {Promise} - { detail: string }
   */
  removeFavorite: (id) => {
    return api.delete(`/favorite-locations/${id}/`);
  },

  /**
   * Get user's connected social accounts (Google, etc.)
   * @returns {Promise} - { social_accounts: Array, count: number }
   */
  getSocialAccounts: () => {
    return api.get('/profile/social-accounts/');
  },

  /**
   * Disconnect a social account
   * @param {number} accountId - Social account ID
   * @returns {Promise} - { detail: string, provider: string }
   */
  disconnectSocialAccount: (accountId) => {
    return api.delete(`/profile/disconnect-social/${accountId}/`);
  },
};

export default profileApi;
