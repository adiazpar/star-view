import { useState, useEffect } from 'react';
import authApi from '../services/auth';

/**
 * Custom hook for managing authentication state
 *
 * Checks authentication status via /api/auth/status/ endpoint
 * and provides user information when authenticated.
 *
 * @returns {Object} Authentication state and methods
 *   - isAuthenticated: boolean - Whether user is logged in
 *   - user: Object|null - User information (id, username, email, first_name, last_name, profile_picture_url)
 *   - loading: boolean - Whether auth check is in progress
 *   - logout: Function - Logout function
 *   - refreshAuth: Function - Re-check authentication status
 */
export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check authentication status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  /**
   * Check if user is authenticated by calling /api/auth/status/
   */
  const checkAuthStatus = async () => {
    try {
      const response = await authApi.checkStatus();
      const data = response.data;

      setIsAuthenticated(data.authenticated);
      setUser(data.user);
    } catch (error) {
      console.error('Error checking auth status:', error);
      // If request fails, assume not authenticated
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Logout user
   */
  const logout = async () => {
    try {
      const response = await authApi.logout();
      const data = response.data;

      // Update local state
      setIsAuthenticated(false);
      setUser(null);

      // Redirect to home page or specified redirect URL
      window.location.href = data.redirect_url || '/';
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  return {
    isAuthenticated,
    user,
    loading,
    logout,
    refreshAuth: checkAuthStatus
  };
}
