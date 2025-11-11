import React from 'react';
import './ProfileHeader.css';

/**
 * ProfileHeader Component
 *
 * Displays user profile header with avatar, name, username, bio, location, and join date.
 * Used by both private ProfilePage and public PublicProfilePage.
 *
 * Props:
 * - user: User object with profile data
 * - isOwnProfile: Boolean indicating if viewing own profile (shows action button)
 * - onEditPage: Boolean indicating if currently on the edit/settings page (shows "Back to Profile" instead of "Edit Profile")
 */
function ProfileHeader({ user, isOwnProfile = false, onEditPage = false }) {
  // Get profile picture URL (use default if none set)
  const profilePictureUrl = user?.profile_picture_url || '/images/default_profile_pic.jpg';

  // Format join date
  const joinDate = user?.date_joined
    ? new Date(user.date_joined).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long'
      })
    : '';

  return (
    <div className="profile-header">
      <div className="profile-header-content">
        {/* Profile Picture */}
        <div className="profile-avatar-large">
          <img
            src={profilePictureUrl}
            alt={`${user?.username}'s profile`}
            className="profile-avatar-img"
          />
        </div>

        {/* User Info */}
        <div className="profile-header-info">
          <div className="profile-name-username-row">
            <div className="profile-name-container">
              <div className="profile-name">
                {user?.first_name && user?.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : 'No name set'
                }
              </div>
              <p className="profile-username">@{user?.username}</p>
            </div>
            {user?.is_verified && (
              <div className="verification-badge">
                <i className="fa-solid fa-circle-check"></i>
              </div>
            )}
          </div>

          {/* Metadata Row */}
          <div className="profile-metadata">
            {user?.location && (
              <span className="profile-metadata-item">
                <i className="fa-solid fa-map-marker-alt"></i>
                {user.location}
              </span>
            )}
            <span className="profile-metadata-item">
              <i className="fa-solid fa-calendar-days"></i>
              Joined {joinDate}
            </span>
          </div>
        </div>
      </div>

      {/* Bio - Below header content */}
      {user?.bio && (
        <p className="profile-bio">{user.bio}</p>
      )}

      {/* Action Buttons (only shown to profile owner) */}
      {isOwnProfile && (
        <div className="profile-actions">
          {onEditPage ? (
            // On edit page: Show "Back to Profile" button
            <a href={`/users/${user?.username}`} className="btn">
              Back to Profile
            </a>
          ) : (
            // On public profile: Show "Edit Profile" button
            <a href="/profile" className="btn">
              Edit Profile
            </a>
          )}
          <a href="/profile" className="btn">
            Placeholder
          </a>
        </div>
      )}
    </div>
  );
}

export default ProfileHeader;
