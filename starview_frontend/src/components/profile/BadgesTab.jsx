import { useState, useEffect } from 'react';
import profileApi from '../../services/profile';
import Alert from '../Alert';
import BadgeCard from '../badges/BadgeCard';
import './BadgesTab.css';

/**
 * BadgesTab - User's badge collection display
 *
 * Shows earned, in-progress, and locked badges
 * Allows pinning/unpinning of earned badges
 */
function BadgesTab({ pinnedBadgesHook }) {
  const [badgeData, setBadgeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Destructure the pinned badges hook passed from parent
  const {
    pinnedBadgeIds,
    togglePin,
    error: pinError,
    successMessage: pinSuccess,
    clearMessages
  } = pinnedBadgesHook;

  // Fetch badge collection data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const badgeResponse = await profileApi.getMyBadgeCollection();
        setBadgeData(badgeResponse.data);
      } catch (err) {
        console.error('Error fetching badges:', err);
        setError('Could not load badge data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle pin/unpin
  const handlePinToggle = async (badgeId) => {
    await togglePin(badgeId);
  };

  // Only show loading for initial badge data fetch, not for pin operations
  if (loading) {
    return (
      <div className="profile-section">
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
          <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '2rem' }}></i>
          <p style={{ marginTop: '16px' }}>Loading badges...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="profile-section">
        <Alert type="error" message={error} onClose={() => setError(null)} />
      </div>
    );
  }

  const { earned, in_progress, locked } = badgeData;
  const totalBadges = (earned?.length || 0) + (in_progress?.length || 0) + (locked?.length || 0);

  return (
    <div className="profile-section">
      <h2 className="profile-section-title">My Badges</h2>
      <p className="profile-section-description">
        Track your achievements and progress
      </p>

      {/* Pin Status Messages */}
      {pinError && (
        <Alert type="error" message={pinError} onClose={clearMessages} />
      )}
      {pinSuccess && (
        <Alert type="success" message={pinSuccess} onClose={clearMessages} />
      )}

      {/* Pinned Badges Summary */}
      {pinnedBadgeIds.length > 0 && (
        <div className="badge-pinned-summary">
          <h3>
            <i className="fa-solid fa-thumbtack"></i> Pinned Badges ({pinnedBadgeIds.length}/3)
          </h3>
          <p>These badges are displayed on your public profile</p>
        </div>
      )}

      {/* Badge Summary Stats */}
      <div className="badge-summary-stats">
        <div className="badge-stat-card">
          <span className="badge-stat-value">{earned?.length || 0}</span>
          <span className="badge-stat-label">Earned</span>
        </div>
        <div className="badge-stat-card">
          <span className="badge-stat-value">{in_progress?.length || 0}</span>
          <span className="badge-stat-label">In Progress</span>
        </div>
        <div className="badge-stat-card">
          <span className="badge-stat-value">{locked?.length || 0}</span>
          <span className="badge-stat-label">Locked</span>
        </div>
        <div className="badge-stat-card">
          <span className="badge-stat-value">{totalBadges}</span>
          <span className="badge-stat-label">Total</span>
        </div>
      </div>

      {/* Earned Badges */}
      {earned && earned.length > 0 && (
        <div className="badge-collection-section">
          <h3>
            <i className="fa-solid fa-check-circle"></i> Earned Badges ({earned.length})
          </h3>
          <p>Badges you have unlocked</p>
          <div className="badge-grid">
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
        </div>
      )}

      {/* In-Progress Badges */}
      {in_progress && in_progress.length > 0 && (
        <div className="badge-collection-section">
          <h3>
            <i className="fa-solid fa-spinner"></i> In-Progress Badges ({in_progress.length})
          </h3>
          <p>Badges with partial progress toward completion</p>
          <div className="badge-grid">
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
        </div>
      )}

      {/* Locked Badges */}
      {locked && locked.length > 0 && (
        <div className="badge-collection-section">
          <h3>
            <i className="fa-solid fa-lock"></i> Locked Badges ({locked.length})
          </h3>
          <p>Badges that haven't been started yet</p>
          <div className="badge-grid">
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
        </div>
      )}
    </div>
  );
}

export default BadgesTab;
