import { useState, useCallback, useEffect } from 'react';
import { profileApi } from '../services/profile';

/**
 * usePinnedBadges - Custom hook for managing pinned badges
 *
 * Provides state management and operations for pinning/unpinning badges.
 * Enforces the 3-badge maximum limit before making API calls.
 * Automatically fetches pinned badges from user profile on mount.
 *
 * @param {boolean} autoFetch - Whether to automatically fetch pinned badges on mount (default: true)
 * @returns {Object} Hook interface
 *   - pinnedBadgeIds: Current array of pinned badge IDs
 *   - isPinned: Function to check if a badge is pinned
 *   - togglePin: Function to pin/unpin a badge
 *   - isLoading: Boolean indicating if an operation is in progress
 *   - error: Error message if operation failed
 *   - successMessage: Success message after operation
 *   - fetchPinnedBadges: Function to manually refetch pinned badges
 */
export function usePinnedBadges(autoFetch = true) {
  const [pinnedBadgeIds, setPinnedBadgeIds] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(autoFetch); // Start as true if auto-fetching
  const [isInitialized, setIsInitialized] = useState(!autoFetch); // Track if initial fetch completed
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  /**
   * Fetch pinned badges from user profile
   * @returns {Promise<Array>} Array of pinned badge IDs
   */
  const fetchPinnedBadges = useCallback(async () => {
    setIsFetching(true);
    try {
      const response = await profileApi.getMe();
      const ids = response.data.pinned_badge_ids || [];
      setPinnedBadgeIds(ids);
      setIsInitialized(true);
      return ids;
    } catch (err) {
      console.error('Error fetching pinned badges:', err);
      setIsInitialized(true); // Mark as initialized even on error
      return [];
    } finally {
      setIsFetching(false);
    }
  }, []);

  // Auto-fetch on mount if enabled
  useEffect(() => {
    if (autoFetch) {
      fetchPinnedBadges();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  /**
   * Check if a badge is currently pinned
   * @param {number} badgeId - Badge ID to check
   * @returns {boolean} True if badge is pinned
   */
  const isPinned = useCallback((badgeId) => {
    return pinnedBadgeIds.includes(badgeId);
  }, [pinnedBadgeIds]);

  /**
   * Toggle pin status for a badge
   * @param {number} badgeId - Badge ID to toggle
   * @returns {Promise<boolean>} True if operation succeeded
   */
  const togglePin = useCallback(async (badgeId) => {
    // Clear previous messages
    setError('');
    setSuccessMessage('');

    const currentlyPinned = pinnedBadgeIds.includes(badgeId);

    // If trying to pin a new badge, check the 3-badge limit
    if (!currentlyPinned && pinnedBadgeIds.length >= 3) {
      setError('You can only pin up to 3 badges. Unpin one first to pin another.');
      return false;
    }

    setIsLoading(true);

    try {
      // Calculate new pinned array
      const newPinnedIds = currentlyPinned
        ? pinnedBadgeIds.filter(id => id !== badgeId) // Unpin
        : [...pinnedBadgeIds, badgeId]; // Pin

      // Call API to update pinned badges
      const response = await profileApi.updatePinnedBadges({
        pinned_badge_ids: newPinnedIds
      });

      // Update local state with response from backend
      setPinnedBadgeIds(response.data.pinned_badge_ids);

      // Set success message
      if (currentlyPinned) {
        setSuccessMessage('Badge unpinned successfully!');
      } else {
        setSuccessMessage('Badge pinned successfully!');
      }

      return true;
    } catch (err) {
      console.error('Error toggling pin:', err);
      const errorMsg = err.response?.data?.detail
        || err.response?.data?.message
        || 'Failed to update pinned badges. Please try again.';
      setError(errorMsg);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [pinnedBadgeIds]);

  /**
   * Clear error and success messages
   */
  const clearMessages = useCallback(() => {
    setError('');
    setSuccessMessage('');
  }, []);

  /**
   * Manually update pinned badge IDs (useful for external updates)
   * @param {Array} newPinnedIds - New array of pinned badge IDs
   */
  const updatePinnedBadgeIds = useCallback((newPinnedIds) => {
    setPinnedBadgeIds(newPinnedIds);
  }, []);

  return {
    pinnedBadgeIds,
    isPinned,
    togglePin,
    isLoading: isLoading || isFetching || !isInitialized,
    error,
    successMessage,
    clearMessages,
    updatePinnedBadgeIds,
    fetchPinnedBadges
  };
}

export default usePinnedBadges;
