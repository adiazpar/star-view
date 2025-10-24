/**
 * Profile page initialization
 *
 * Initializes the profile page by importing API endpoints from the
 * central config and passing them to the profile module.
 */

import { initProfilePage } from './account_profile.js';
import { API_ENDPOINTS } from '../../utils/util_config.js';

// Initialize profile page with API endpoints from config
document.addEventListener('DOMContentLoaded', () => {
    const profileConfig = {
        urls: {
            uploadProfilePicture: API_ENDPOINTS.profile.uploadPicture,
            removeProfilePicture: API_ENDPOINTS.profile.removePicture,
            updateName: API_ENDPOINTS.profile.updateName,
            changeEmail: API_ENDPOINTS.profile.updateEmail,
            changePassword: API_ENDPOINTS.profile.updatePassword
        }
    };

    initProfilePage(profileConfig);
});
