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

    // Favorite locations endpoints (legacy naming from API)
    favoriteLocations: {
        base: '/api/favorite-locations/',
        detail: (id) => `/api/favorite-locations/${id}/`,
    },

    // Location-specific review and comment endpoints
    location: {
        reviews: (locationId) => `/api/locations/${locationId}/reviews/`,
        reviewDetail: (locationId, reviewId) => `/api/locations/${locationId}/reviews/${reviewId}/`,
        reviewPhotos: (locationId, reviewId) => `/api/locations/${locationId}/reviews/${reviewId}/add_photos/`,
        reviewPhotoDelete: (locationId, reviewId, photoId) => `/api/locations/${locationId}/reviews/${reviewId}/photos/${photoId}/`,
        reviewVote: (locationId, reviewId) => `/api/locations/${locationId}/reviews/${reviewId}/vote/`,
        reviewReport: (locationId, reviewId) => `/api/locations/${locationId}/reviews/${reviewId}/report/`,
        comments: (locationId, reviewId) => `/api/locations/${locationId}/reviews/${reviewId}/comments/`,
        commentDetail: (locationId, reviewId, commentId) =>
            `/api/locations/${locationId}/reviews/${reviewId}/comments/${commentId}/`,
        commentVote: (locationId, reviewId, commentId) =>
            `/api/locations/${locationId}/reviews/${reviewId}/comments/${commentId}/vote/`,
        commentReport: (locationId, reviewId, commentId) =>
            `/api/locations/${locationId}/reviews/${reviewId}/comments/${commentId}/report/`,
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
