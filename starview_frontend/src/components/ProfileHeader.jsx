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
          <div className="profile-header-top">
            <div>
              <h1 className="profile-username">{user?.username}</h1>
              <p className="profile-name">
                {user?.first_name && user?.last_name
                  ? `${user.first_name} ${user.last_name}`
                  : 'No name set'
                }
              </p>
            </div>

            {/* Action Button (only shown to profile owner) */}
            {isOwnProfile && (
              onEditPage ? (
                // On edit page: Show "Back to Profile" button
                <a href={`/users/${user?.username}`} className="btn btn-secondary">
                  <i className="fa-solid fa-arrow-left"></i>
                  Back to Profile
                </a>
              ) : (
                // On public profile: Show "Edit Profile" button
                <a href="/profile" className="btn btn-primary">
                  <i className="fa-solid fa-gear"></i>
                  Edit Profile
                </a>
              )
            )}
          </div>

          {/* Bio */}
          {user?.bio && (
            <p className="profile-bio">{user.bio}</p>
          )}

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
              Member since {joinDate}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProfileHeader;
