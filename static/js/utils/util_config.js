/**
 * Central configuration file for API endpoints and application settings
 *
 * This file serves as the single source of truth for all API endpoint URLs
 * used throughout the application. By centralizing these URLs, we ensure
 * consistency and make it easier to update endpoints across the entire app.
 */

export const API_ENDPOINTS = {
    // Profile management endpoints
    profile: {
        uploadPicture: '/api/profile/upload-picture/',
        removePicture: '/api/profile/remove-picture/',
        updateName: '/api/profile/update-name/',
        updateEmail: '/api/profile/update-email/',
        updatePassword: '/api/profile/update-password/',
    },

    // Location endpoints
    locations: {
        base: '/api/locations/',
        detail: (id) => `/api/locations/${id}/`,
        favorite: (id) => `/api/locations/${id}/favorite/`,
        unfavorite: (id) => `/api/locations/${id}/unfavorite/`,
    },

    // Review endpoints
    reviews: {
        base: '/api/reviews/',
        detail: (id) => `/api/reviews/${id}/`,
        vote: (id) => `/api/reviews/${id}/vote/`,
    },

    // Comment endpoints
    comments: {
        base: '/api/comments/',
        detail: (id) => `/api/comments/${id}/`,
        vote: (id) => `/api/comments/${id}/vote/`,
    },

    // Favorite endpoints
    favorites: {
        base: '/api/favorites/',
        detail: (id) => `/api/favorites/${id}/`,
    },

    // Report endpoints
    reports: {
        base: '/api/reports/',
    },

    // Authentication endpoints
    auth: {
        login: '/login/',
        register: '/register/',
        logout: '/logout/',
    },
};

/**
 * Get CSRF token from the page
 * @returns {string} The CSRF token value
 */
export function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}
