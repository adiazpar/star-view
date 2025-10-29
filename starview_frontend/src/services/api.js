/**
 * API Client Configuration
 *
 * This file sets up Axios to communicate with the Django backend.
 * It handles:
 * - CSRF token extraction from cookies (Django requirement)
 * - Session-based authentication (sends cookies)
 * - Automatic error handling
 */

import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true, // Important: sends cookies for Django session auth
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * Adds CSRF token to all non-GET requests
 */
api.interceptors.request.use(
  (config) => {
    // Django requires CSRF token for POST, PUT, PATCH, DELETE
    if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
      const csrfToken = getCookie('csrftoken');
      if (csrfToken) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * Handles common error scenarios
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized - redirect to login
    if (error.response?.status === 401) {
      console.warn('Unauthorized - redirecting to login');
      // You can redirect here or let components handle it
      // window.location.href = '/login';
    }

    // Handle 403 Forbidden
    if (error.response?.status === 403) {
      console.error('Forbidden - check permissions');
    }

    // Handle 500 Server Error
    if (error.response?.status === 500) {
      console.error('Server error - try again later');
    }

    return Promise.reject(error);
  }
);

/**
 * Helper function to extract CSRF token from cookies
 * Django stores it as 'csrftoken' cookie
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export default api;
