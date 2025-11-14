import React, { useState, useEffect } from 'react';
import BadgeCard from '../components/badges/BadgeCard';
import profileApi from '../services/profile';
import usePinnedBadges from '../hooks/usePinnedBadges';
import Alert from '../components/Alert';
import './BadgeTestPage.css';

/**
 * BadgeTestPage - Test page to preview badge components
 * Shows full badge cards for all earned, in-progress, and locked badges
 */
function BadgeTestPage() {
  const [badgeData, setBadgeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Use the pinned badges hook (auto-fetches on mount)
  const {
    pinnedBadgeIds,
    isPinned,
    togglePin,
    isLoading: pinLoading,
    error: pinError,
    successMessage: pinSuccess,
    clearMessages
  } = usePinnedBadges(true); // autoFetch = true

  // Fetch badge collection data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const badgeResponse = await profileApi.getMyBadgeCollection();
        setBadgeData(badgeResponse.data);
      } catch (err) {
        // If not authenticated or error, show error message
        console.error('Error fetching data:', err);
        setError('Could not load data. Make sure you are logged in.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading || pinLoading) {
    return (
      <div className="badge-test-page">
        <div className="container">
          <h1>Badge System Preview</h1>
          <p className="subtitle">Loading real badge data from backend...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="badge-test-page">
        <div className="container">
          <h1>Badge System Preview</h1>
          <p className="subtitle error">{error}</p>
        </div>
      </div>
    );
  }

  const { earned, in_progress, locked } = badgeData;

  // Handle pin/unpin from badge cards
  const handlePinToggle = async (badgeId) => {
    await togglePin(badgeId);
  };

  return (
    <div className="badge-test-page">
      <div className="container">
        <h1>Badge System Preview</h1>
        <p className="subtitle">Real badge data from backend API - Full badge cards</p>

        {/* Pin Status Messages */}
        {pinError && (
          <Alert type="error" message={pinError} onClose={clearMessages} />
        )}
        {pinSuccess && (
          <Alert type="success" message={pinSuccess} onClose={clearMessages} />
        )}

        {/* Pinned Badges Summary */}
        {pinnedBadgeIds.length > 0 && (
          <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius)' }}>
            <h3 style={{ marginBottom: '8px' }}>📌 Pinned Badges ({pinnedBadgeIds.length}/3)</h3>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>
              Badge IDs: {pinnedBadgeIds.join(', ')}
            </p>
          </div>
        )}

            {/* Earned Badges */}
        {earned && earned.length > 0 && (
          <section className="badge-test-section">
            <h2>
              <i className="fa-solid fa-check-circle"></i> Earned Badges ({earned.length})
            </h2>
            <p>Badges you have unlocked</p>
            <div className="badge-test-grid">
              {earned.map(item => (
                <BadgeCard
                  key={item.badge_id}
                  badge={{
                    id: item.badge_id,
                    name: item.name,
                    slug: item.slug,
                    description: item.description,
                    category: item.category,
                    tier: item.tier,
                    is_rare: item.is_rare,
                    icon_path: item.icon_path
                  }}
                  state="earned"
                  earnedAt={item.earned_at}
                  isPinned={pinnedBadgeIds.includes(item.badge_id)}
                  canPin={true}
                  onPin={handlePinToggle}
                />
              ))}
            </div>
          </section>
        )}

        {/* In-Progress Badges */}
        {in_progress && in_progress.length > 0 && (
          <section className="badge-test-section">
            <h2>
              <i className="fa-solid fa-spinner"></i> In-Progress Badges ({in_progress.length})
            </h2>
            <p>Badges with partial progress toward completion</p>
            <div className="badge-test-grid">
              {in_progress.map(item => (
                <BadgeCard
                  key={item.badge_id}
                  badge={{
                    id: item.badge_id,
                    name: item.name,
                    slug: item.slug,
                    description: item.description,
                    category: item.category,
                    tier: item.tier,
                    is_rare: item.is_rare,
                    icon_path: item.icon_path
                  }}
                  state="in-progress"
                  progress={{
                    current: item.current_progress,
                    total: item.criteria_value,
                    percentage: item.percentage
                  }}
                />
              ))}
            </div>
          </section>
        )}

        {/* Locked Badges */}
        {locked && locked.length > 0 && (
          <section className="badge-test-section">
            <h2>
              <i className="fa-solid fa-lock"></i> Locked Badges ({locked.length})
            </h2>
            <p>Badges that haven't been started yet</p>
            <div className="badge-test-grid">
              {locked.map(item => (
                <BadgeCard
                  key={item.badge_id}
                  badge={{
                    id: item.badge_id,
                    name: item.name,
                    slug: item.slug,
                    description: item.description,
                    category: item.category,
                    tier: item.tier,
                    is_rare: item.is_rare,
                    icon_path: item.icon_path
                  }}
                  state="locked"
                />
              ))}
            </div>
          </section>
        )}

        {/* Summary */}
        <section className="badge-test-section">
          <h2>
            <i className="fa-solid fa-chart-pie"></i> Badge Summary
          </h2>
          <div className="badge-summary">
            <div className="summary-stat">
              <span className="stat-value">{earned?.length || 0}</span>
              <span className="stat-label">Earned</span>
            </div>
            <div className="summary-stat">
              <span className="stat-value">{in_progress?.length || 0}</span>
              <span className="stat-label">In Progress</span>
            </div>
            <div className="summary-stat">
              <span className="stat-value">{locked?.length || 0}</span>
              <span className="stat-label">Locked</span>
            </div>
            <div className="summary-stat">
              <span className="stat-value">{(earned?.length || 0) + (in_progress?.length || 0) + (locked?.length || 0)}</span>
              <span className="stat-label">Total</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

export default BadgeTestPage;
