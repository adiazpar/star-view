import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import profileApi from '../services/profile';
import { mapBadgeIdsToBadges } from '../utils/badgeUtils';
import usePinnedBadges from '../hooks/usePinnedBadges';
import Alert from '../components/Alert';
import ProfileHeader from '../components/ProfileHeader';
import ProfileSettings from '../components/profile/ProfileSettings';
import PreferencesSection from '../components/profile/PreferencesSection';
import ConnectedAccountsSection from '../components/profile/ConnectedAccountsSection';
import BadgesTab from '../components/profile/BadgesTab';
import MyReviewsTab from '../components/profile/MyReviewsTab';
import FavoritesTab from '../components/profile/FavoritesTab';
import './ProfilePage.css';

function ProfilePage() {
  const { user, refreshAuth } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('settings');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [pinnedBadges, setPinnedBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  // Use the pinned badges hook at the top level
  const pinnedBadgesHook = usePinnedBadges(true);

  // Fetch pinned badges and map them to badge objects for the header
  useEffect(() => {
    const fetchPinnedBadges = async () => {
      setLoading(true);
      try {
        const badgesResponse = await profileApi.getMyBadgeCollection();
        const earnedBadges = badgesResponse.data.earned || [];
        const pinned = mapBadgeIdsToBadges(pinnedBadgesHook.pinnedBadgeIds, earnedBadges);
        setPinnedBadges(pinned);
      } catch (err) {
        console.error('Error fetching pinned badges:', err);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch when pinnedBadgeIds changes
    if (pinnedBadgesHook.pinnedBadgeIds.length >= 0) {
      fetchPinnedBadges();
    }
  }, [pinnedBadgesHook.pinnedBadgeIds]);

  // Check for social account connection success/errors
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('social_connected') === 'true') {
      setSuccessMessage('Social account connected successfully!');
      navigate('/profile', { replace: true });
    }
    if (params.get('social_disconnected') === 'true') {
      setSuccessMessage('Social account disconnected successfully!');
      navigate('/profile', { replace: true });
    }
    if (params.get('error') === 'email_conflict') {
      setErrorMessage('This social account is already registered to another user.');
      navigate('/profile', { replace: true });
    }
    if (params.get('error') === 'social_already_connected') {
      setErrorMessage('This social account is already connected to another user.');
      navigate('/profile', { replace: true });
    }
  }, [location.search, navigate]);

  // Loading state
  if (loading) {
    return (
      <div className="profile-page">
        <div className="profile-container">
          <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
            <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '2rem' }}></i>
            <p style={{ marginTop: '16px' }}>Loading profile...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-container">
        {/* Profile Header - Using Shared Component */}
        <ProfileHeader
          user={user}
          isOwnProfile={true}
          onEditPage={true}
          pinnedBadges={pinnedBadges}
        />

        {/* Success Message */}
        {successMessage && (
          <Alert
            type="success"
            message={successMessage}
            onClose={() => setSuccessMessage('')}
          />
        )}

        {/* Error Message */}
        {errorMessage && (
          <Alert
            type="error"
            message={errorMessage}
            onClose={() => setErrorMessage('')}
          />
        )}

        {/* Tab Navigation */}
        <div className="profile-tabs">
          <button
            className={`profile-tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            <i className="fa-solid fa-gear"></i>
            <span className="profile-tab-text">Settings</span>
          </button>
          <button
            className={`profile-tab ${activeTab === 'badges' ? 'active' : ''}`}
            onClick={() => setActiveTab('badges')}
          >
            <i className="fa-solid fa-award"></i>
            <span className="profile-tab-text">Badges</span>
          </button>
          <button
            className={`profile-tab ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            <i className="fa-solid fa-star"></i>
            <span className="profile-tab-text">My Reviews</span>
          </button>
          <button
            className={`profile-tab ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => setActiveTab('favorites')}
          >
            <i className="fa-solid fa-heart"></i>
            <span className="profile-tab-text">Favorites</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="profile-content">
          {activeTab === 'settings' && (
            <div className="profile-section">
              <ProfileSettings user={user} refreshAuth={refreshAuth} />
              <PreferencesSection />
              <ConnectedAccountsSection />
            </div>
          )}
          {activeTab === 'badges' && (
            <BadgesTab user={user} pinnedBadgesHook={pinnedBadgesHook} />
          )}
          {activeTab === 'reviews' && (
            <MyReviewsTab />
          )}
          {activeTab === 'favorites' && (
            <FavoritesTab />
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
