import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import profileApi from '../services/profile';
import Alert from '../components/Alert';
import ProfileHeader from '../components/ProfileHeader';
import './ProfilePage.css';

function ProfilePage() {
  const { user, refreshAuth } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('settings');
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

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

  return (
    <div className="profile-page">
      <div className="profile-container">
        {/* Profile Header - Using Shared Component */}
        <ProfileHeader user={user} isOwnProfile={true} onEditPage={true} />

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
            Settings
          </button>
          <button
            className={`profile-tab ${activeTab === 'reviews' ? 'active' : ''}`}
            onClick={() => setActiveTab('reviews')}
          >
            <i className="fa-solid fa-star"></i>
            My Reviews
          </button>
          <button
            className={`profile-tab ${activeTab === 'favorites' ? 'active' : ''}`}
            onClick={() => setActiveTab('favorites')}
          >
            <i className="fa-solid fa-heart"></i>
            Favorites
          </button>
        </div>

        {/* Tab Content */}
        <div className="profile-content">
          {activeTab === 'settings' && (
            <ProfileSettings user={user} refreshAuth={refreshAuth} />
          )}
          {activeTab === 'reviews' && (
            <MyReviews user={user} />
          )}
          {activeTab === 'favorites' && (
            <FavoritesTab user={user} />
          )}
        </div>
      </div>
    </div>
  );
}

// Profile Settings Component
function ProfileSettings({ user, refreshAuth }) {
  const [loading, setLoading] = useState(false);

  // Section-specific alert states
  const [pictureSuccess, setPictureSuccess] = useState('');
  const [pictureError, setPictureError] = useState('');
  const [nameSuccess, setNameSuccess] = useState('');
  const [nameError, setNameError] = useState('');
  const [usernameSuccess, setUsernameSuccess] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [emailSuccess, setEmailSuccess] = useState('');
  const [emailError, setEmailError] = useState('');
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [bioSuccess, setBioSuccess] = useState('');
  const [bioError, setBioError] = useState('');
  const [locationSuccess, setLocationSuccess] = useState('');
  const [locationError, setLocationError] = useState('');

  const [profilePicture, setProfilePicture] = useState(user?.profile_picture_url || '/images/default_profile_pic.jpg');

  // Personal info state
  const [personalInfo, setPersonalInfo] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  });

  // Username state
  const [username, setUsername] = useState(user?.username || '');

  // Bio and Location state
  const [bio, setBio] = useState(user?.bio || '');
  const [locationField, setLocationField] = useState(user?.location || '');

  // Update profile picture when user data changes (e.g., after page refresh or refreshAuth)
  useEffect(() => {
    if (user?.profile_picture_url) {
      setProfilePicture(user.profile_picture_url);
    }
  }, [user?.profile_picture_url]);

  // Update personal info when user data changes (e.g., after page refresh or refreshAuth)
  useEffect(() => {
    if (user) {
      setPersonalInfo({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
      });
      setUsername(user.username || '');
      setBio(user.bio || '');
      setLocationField(user.location || '');
    }
  }, [user]);

  // Password state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });

  // Handle profile picture upload
  const handlePictureUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Clear previous messages
    setPictureSuccess('');
    setPictureError('');

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      setPictureError('Image must be less than 5MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setPictureError('Please upload an image file');
      return;
    }

    setLoading(true);
    try {
      const response = await profileApi.uploadProfilePicture(file);
      setProfilePicture(response.data.image_url);
      setPictureSuccess('Profile picture updated successfully!');
      await refreshAuth(); // Refresh auth to update navbar avatar
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to upload image';
      setPictureError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle profile picture removal
  const handlePictureRemove = async () => {
    if (!confirm('Are you sure you want to remove your profile picture?')) return;

    // Clear previous messages
    setPictureSuccess('');
    setPictureError('');

    setLoading(true);
    try {
      const response = await profileApi.removeProfilePicture();
      setProfilePicture(response.data.default_image_url);
      setPictureSuccess('Profile picture removed successfully!');
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to remove image';
      setPictureError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle personal info update
  const handlePersonalInfoUpdate = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setNameSuccess('');
    setNameError('');

    setLoading(true);
    try {
      await profileApi.updateName({
        first_name: personalInfo.first_name,
        last_name: personalInfo.last_name,
      });
      setNameSuccess('Name updated successfully!');
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update name';
      setNameError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle username update
  const handleUsernameUpdate = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setUsernameSuccess('');
    setUsernameError('');

    setLoading(true);
    try {
      await profileApi.updateUsername({
        new_username: username,
      });
      setUsernameSuccess('Username updated successfully!');
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update username';
      setUsernameError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle email update
  const handleEmailUpdate = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setEmailSuccess('');
    setEmailError('');

    setLoading(true);
    try {
      const response = await profileApi.updateEmail({
        new_email: personalInfo.email,
      });

      // Check if verification is required
      if (response.data.verification_required) {
        setEmailSuccess(response.data.detail);
        // Note: Email won't change until user verifies the new address
      } else {
        setEmailSuccess('Email updated successfully!');
        await refreshAuth();
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update email';
      setEmailError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle password update
  const handlePasswordUpdate = async (e) => {
    e.preventDefault();

    // Clear previous password messages
    setPasswordSuccess('');
    setPasswordError('');

    // Validate passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordError('New passwords do not match');
      return;
    }

    // Validate password length
    if (passwordData.new_password.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await profileApi.updatePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setPasswordSuccess('Password updated successfully!');
      // Clear password fields
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      // Refresh user data to update has_usable_password status
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update password';
      setPasswordError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle bio update
  const handleBioUpdate = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setBioSuccess('');
    setBioError('');

    setLoading(true);
    try {
      await profileApi.updateBio({ bio });
      setBioSuccess('Bio updated successfully!');
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update bio';
      setBioError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Handle location update
  const handleLocationUpdate = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setLocationSuccess('');
    setLocationError('');

    setLoading(true);
    try {
      await profileApi.updateLocation({ location: locationField });
      setLocationSuccess('Location updated successfully!');
      await refreshAuth();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to update location';
      setLocationError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-section">
      <h2 className="profile-section-title">Profile Settings</h2>
      <p className="profile-section-description">
        Manage your account settings and profile information
      </p>

      <div className="profile-settings-grid">
        {/* Profile Picture Section */}
        <div className="profile-picture-section">
          <h3>Profile Picture</h3>

          {/* Profile Picture Success/Error Messages */}
          {pictureSuccess && (
            <Alert
              type="success"
              message={pictureSuccess}
              onClose={() => setPictureSuccess('')}
            />
          )}
          {pictureError && (
            <Alert
              type="error"
              message={pictureError}
              onClose={() => setPictureError('')}
            />
          )}

          <div className="profile-picture-upload">
            <div className="profile-picture-preview">
              <img src={profilePicture} alt="Profile" />
            </div>
            <div className="profile-picture-actions">
              <div className="profile-picture-buttons">
                <label htmlFor="profile-picture-input" className="btn btn-primary">
                  <i className="fa-solid fa-upload"></i>
                  Upload Photo
                </label>
                <input
                  id="profile-picture-input"
                  type="file"
                  accept="image/*"
                  onChange={handlePictureUpload}
                  className="profile-file-input"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={handlePictureRemove}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  <i className="fa-solid fa-trash"></i>
                  Remove
                </button>
              </div>
              <p className="profile-picture-help">
                JPG, PNG or GIF. Max size 5MB.
              </p>
            </div>
          </div>
        </div>

        {/* Personal Information Section */}
        <div className="profile-form-section">
          <h3>Personal Information</h3>

          {/* Name Success/Error Messages */}
          {nameSuccess && (
            <Alert
              type="success"
              message={nameSuccess}
              onClose={() => setNameSuccess('')}
            />
          )}
          {nameError && (
            <Alert
              type="error"
              message={nameError}
              onClose={() => setNameError('')}
            />
          )}

          <form onSubmit={handlePersonalInfoUpdate}>
            <div className="profile-form-grid">
              <div className="profile-form-row">
                <div className="form-group">
                  <label htmlFor="first-name" className="form-label">First Name</label>
                  <input
                    type="text"
                    id="first-name"
                    className="form-input"
                    value={personalInfo.first_name}
                    onChange={(e) => setPersonalInfo({ ...personalInfo, first_name: e.target.value })}
                    required
                    disabled={loading}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="last-name" className="form-label">Last Name</label>
                  <input
                    type="text"
                    id="last-name"
                    className="form-input"
                    value={personalInfo.last_name}
                    onChange={(e) => setPersonalInfo({ ...personalInfo, last_name: e.target.value })}
                    required
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-save"></i>
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Username Section */}
        <div className="profile-form-section">
          <h3>Username</h3>

          {/* Username Success/Error Messages */}
          {usernameSuccess && (
            <Alert
              type="success"
              message={usernameSuccess}
              onClose={() => setUsernameSuccess('')}
            />
          )}
          {usernameError && (
            <Alert
              type="error"
              message={usernameError}
              onClose={() => setUsernameError('')}
            />
          )}

          <form onSubmit={handleUsernameUpdate}>
            <div className="form-group">
              <label htmlFor="username" className="form-label">Username</label>
              <input
                type="text"
                id="username"
                className="form-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
                placeholder="Enter username"
              />
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '4px' }}>
                <i className="fa-solid fa-circle-info"></i> 3-30 characters. Letters, numbers, underscores, and hyphens only.
              </p>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    Updating...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-save"></i>
                    Update Username
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Email Section */}
        <div className="profile-form-section">
          <h3>Email Address</h3>

          {/* Email Success/Error Messages */}
          {emailSuccess && (
            <Alert
              type="success"
              message={emailSuccess}
              onClose={() => setEmailSuccess('')}
            />
          )}
          {emailError && (
            <Alert
              type="error"
              message={emailError}
              onClose={() => setEmailError('')}
            />
          )}

          <form onSubmit={handleEmailUpdate}>
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email</label>
              <input
                type="email"
                id="email"
                className="form-input"
                value={personalInfo.email}
                onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                required
                disabled={loading}
              />
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '4px' }}>
                <i className="fa-solid fa-shield-halved"></i> For security, you'll need to verify your new email address before the change takes effect
              </p>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    Updating...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-save"></i>
                    Update Email
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Password Section */}
        <div className="profile-form-section">
          <h3>{user?.has_usable_password ? 'Change Password' : 'Set Password'}</h3>
          {!user?.has_usable_password && (
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              <i className="fa-solid fa-info-circle"></i> Set a password to enable password-based login in addition to your social account.
            </p>
          )}

          {/* Password Success/Error Messages */}
          {passwordSuccess && (
            <Alert
              type="success"
              message={passwordSuccess}
              onClose={() => setPasswordSuccess('')}
            />
          )}
          {passwordError && (
            <Alert
              type="error"
              message={passwordError}
              onClose={() => setPasswordError('')}
            />
          )}

          <form onSubmit={handlePasswordUpdate}>
            <div className="profile-form-grid">
              {user?.has_usable_password && (
                <div className="form-group">
                  <label htmlFor="current-password" className="form-label">Current Password</label>
                  <div className="profile-password-input-wrapper">
                    <input
                      type={showPasswords.current ? "text" : "password"}
                      id="current-password"
                      className="form-input"
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      required
                      disabled={loading}
                    />
                    <button
                      type="button"
                      className="profile-password-toggle"
                      onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                      tabIndex={-1}
                    >
                      <i className={`fa-solid ${showPasswords.current ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                    </button>
                  </div>
                </div>
              )}
              <div className="form-group">
                <label htmlFor="new-password" className="form-label">New Password</label>
                <div className="profile-password-input-wrapper">
                  <input
                    type={showPasswords.new ? "text" : "password"}
                    id="new-password"
                    className="form-input"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    required
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="profile-password-toggle"
                    onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                    tabIndex={-1}
                  >
                    <i className={`fa-solid ${showPasswords.new ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label htmlFor="confirm-password" className="form-label">Confirm New Password</label>
                <div className="profile-password-input-wrapper">
                  <input
                    type={showPasswords.confirm ? "text" : "password"}
                    id="confirm-password"
                    className="form-input"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    required
                    disabled={loading}
                  />
                  <button
                    type="button"
                    className="profile-password-toggle"
                    onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                    tabIndex={-1}
                  >
                    <i className={`fa-solid ${showPasswords.confirm ? 'fa-eye-slash' : 'fa-eye'}`}></i>
                  </button>
                </div>
              </div>
            </div>
            <div className="password-requirements">
              <p>Password Requirements:</p>
              <ul>
                <li>At least 8 characters long</li>
                <li>Cannot be too similar to your other personal information</li>
                <li>Cannot be a commonly used password</li>
                <li>Cannot be entirely numeric</li>
              </ul>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    {user?.has_usable_password ? 'Changing...' : 'Setting...'}
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-key"></i>
                    {user?.has_usable_password ? 'Change Password' : 'Set Password'}
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Bio Section */}
        <div className="profile-form-section">
          <h3>Bio</h3>

          {/* Bio Success/Error Messages */}
          {bioSuccess && (
            <Alert
              type="success"
              message={bioSuccess}
              onClose={() => setBioSuccess('')}
            />
          )}
          {bioError && (
            <Alert
              type="error"
              message={bioError}
              onClose={() => setBioError('')}
            />
          )}

          <form onSubmit={handleBioUpdate}>
            <div className="form-group">
              <label htmlFor="bio" className="form-label">About You</label>
              <textarea
                id="bio"
                className="form-input"
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                rows="4"
                maxLength="150"
                placeholder="Tell others about yourself..."
                disabled={loading}
                style={{ resize: 'vertical', minHeight: '100px' }}
              />
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '4px' }}>
                <i className="fa-solid fa-circle-info"></i> {bio.length}/150 characters. This will be visible on your public profile.
              </p>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-save"></i>
                    Save Bio
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Location Section */}
        <div className="profile-form-section">
          <h3>Location</h3>

          {/* Location Success/Error Messages */}
          {locationSuccess && (
            <Alert
              type="success"
              message={locationSuccess}
              onClose={() => setLocationSuccess('')}
            />
          )}
          {locationError && (
            <Alert
              type="error"
              message={locationError}
              onClose={() => setLocationError('')}
            />
          )}

          <form onSubmit={handleLocationUpdate}>
            <div className="form-group">
              <label htmlFor="location" className="form-label">Location</label>
              <input
                type="text"
                id="location"
                className="form-input"
                value={locationField}
                onChange={(e) => setLocationField(e.target.value)}
                maxLength="100"
                placeholder="e.g., Seattle, WA"
                disabled={loading}
              />
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginTop: '4px' }}>
                <i className="fa-solid fa-map-marker-alt"></i> Where are you based? This will be visible on your public profile.
              </p>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <i className="fa-solid fa-spinner fa-spin"></i>
                    Saving...
                  </>
                ) : (
                  <>
                    <i className="fa-solid fa-save"></i>
                    Save Location
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Connected Accounts Section */}
        <ConnectedAccountsSection />
      </div>
    </div>
  );
}

// Connected Accounts Section Component
function ConnectedAccountsSection() {
  const [socialAccounts, setSocialAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchSocialAccounts();
  }, []);

  const fetchSocialAccounts = async () => {
    setLoading(true);
    try {
      const response = await profileApi.getSocialAccounts();
      setSocialAccounts(response.data.social_accounts || []);
    } catch (err) {
      console.error('Error fetching social accounts:', err);
      setError('Failed to load connected accounts');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async (accountId, providerName) => {
    if (!window.confirm(`Are you sure you want to disconnect your ${providerName} account?`)) return;

    try {
      const response = await profileApi.disconnectSocialAccount(accountId);
      setSocialAccounts(socialAccounts.filter(acc => acc.id !== accountId));
      setSuccess(response.data.detail);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Failed to disconnect account';
      setError(errorMessage);
    }
  };

  // Map provider to icon
  const getProviderIcon = (provider) => {
    const iconMap = {
      'google': 'fa-brands fa-google',
      'facebook': 'fa-brands fa-facebook',
      'github': 'fa-brands fa-github',
      'twitter': 'fa-brands fa-twitter',
    };
    return iconMap[provider.toLowerCase()] || 'fa-solid fa-link';
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="profile-form-section">
      <h3>Connected Accounts</h3>
      <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Manage third-party accounts linked to your Starview profile
      </p>

      {/* Success/Error Messages */}
      {success && (
        <Alert
          type="success"
          message={success}
          onClose={() => setSuccess('')}
        />
      )}
      {error && (
        <Alert
          type="error"
          message={error}
          onClose={() => setError('')}
        />
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-secondary)' }}>
          <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '1.5rem' }}></i>
        </div>
      ) : socialAccounts.length > 0 ? (
        <div className="connected-accounts-list">
          {socialAccounts.map((account) => (
            <div key={account.id} className="connected-account-item">
              <div className="connected-account-icon">
                <i className={getProviderIcon(account.provider)}></i>
              </div>
              <div className="connected-account-info">
                <h4>{account.provider_name}</h4>
                <p className="connected-account-email">{account.email}</p>
                <p className="connected-account-date">
                  Connected {formatDate(account.connected_at)}
                </p>
              </div>
              <div className="connected-account-actions">
                <button
                  onClick={() => handleDisconnect(account.id, account.provider_name)}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: 'var(--text-sm)' }}
                >
                  <i className="fa-solid fa-unlink"></i>
                  Disconnect
                </button>
              </div>
            </div>
          ))}
          <div style={{ marginTop: '16px' }}>
            <Alert
              type="info"
              message="Your profile email may differ from your social account email. Both can be used to access your account - your profile email for password login, and your social account for OAuth login."
              showIcon={true}
            />
          </div>
        </div>
      ) : (
        <div className="connected-accounts-empty">
          <i className="fa-solid fa-link-slash" style={{ fontSize: '2rem', color: 'var(--text-muted)', marginBottom: '12px' }}></i>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
            No connected accounts yet
          </p>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginBottom: '20px' }}>
            Link a social account to enable faster login options
          </p>
          <a
            href="/accounts/google/login/?process=connect"
            className="btn btn-primary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}
          >
            <i className="fa-brands fa-google"></i>
            Connect Google Account
          </a>
        </div>
      )}
    </div>
  );
}

function MyReviews({ user }) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // For now, show placeholder since we don't have a direct endpoint for user's reviews
    // This would need a backend endpoint like GET /api/profile/reviews/
    setLoading(false);
  }, []);

  return (
    <div className="profile-section">
      <h2 className="profile-section-title">My Reviews</h2>
      <p className="profile-section-description">
        View and manage your location reviews
      </p>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
          <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '2rem' }}></i>
        </div>
      ) : error ? (
        <Alert
          type="error"
          message={error}
          onClose={() => setError('')}
        />
      ) : (
        <div className="profile-empty-state">
          <i className="fa-solid fa-star"></i>
          <p>Coming Soon!</p>
          <p style={{ fontSize: 'var(--text-sm)', marginTop: '8px' }}>
            Your review history will appear here. This feature requires a backend endpoint for fetching user reviews.
          </p>
        </div>
      )}
    </div>
  );
}

function FavoritesTab({ user }) {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Fetch favorites on mount
  useEffect(() => {
    const fetchFavorites = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await profileApi.getFavorites();
        console.log('Favorites response:', response.data);
        // Handle both array and object responses
        if (Array.isArray(response.data)) {
          setFavorites(response.data);
        } else if (response.data.results) {
          // Paginated response
          setFavorites(response.data.results);
        } else {
          setFavorites([]);
        }
      } catch (err) {
        console.error('Error fetching favorites:', err);
        const errorMessage = err.response?.data?.detail || 'Failed to load favorites';
        setError(errorMessage);
        setFavorites([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFavorites();
  }, []);

  const handleRemoveFavorite = async (favoriteId, locationName) => {
    // eslint-disable-next-line no-restricted-globals
    if (!window.confirm(`Remove "${locationName}" from favorites?`)) return;

    try {
      await profileApi.removeFavorite(favoriteId);
      setFavorites(favorites.filter(fav => fav.id !== favoriteId));
      setSuccess('Favorite removed successfully!');
    } catch (err) {
      console.error('Error removing favorite:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to remove favorite';
      setError(errorMessage);
    }
  };

  return (
    <div className="profile-section">
      <h2 className="profile-section-title">Favorite Locations</h2>
      <p className="profile-section-description">
        Your saved stargazing locations
      </p>

      {/* Success/Error Messages */}
      {success && (
        <Alert
          type="success"
          message={success}
          onClose={() => setSuccess('')}
        />
      )}
      {error && (
        <Alert
          type="error"
          message={error}
          onClose={() => setError('')}
        />
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)' }}>
          <i className="fa-solid fa-spinner fa-spin" style={{ fontSize: '2rem' }}></i>
        </div>
      ) : favorites.length === 0 ? (
        <div className="profile-empty-state">
          <i className="fa-solid fa-heart"></i>
          <p>No favorites yet</p>
          <p style={{ fontSize: 'var(--text-sm)', marginTop: '8px' }}>
            Start exploring locations and save your favorites!
          </p>
        </div>
      ) : (
        <div className="profile-items-grid">
          {favorites.map((favorite) => (
            <div key={favorite.id} className="profile-item-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <h3 style={{
                    fontSize: 'var(--text-lg)',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    marginBottom: '8px'
                  }}>
                    {favorite.location?.name || 'Unknown Location'}
                  </h3>

                  {favorite.nickname && (
                    <p style={{
                      fontSize: 'var(--text-sm)',
                      color: 'var(--accent)',
                      marginBottom: '8px',
                      fontStyle: 'italic'
                    }}>
                      <i className="fa-solid fa-tag"></i> {favorite.nickname}
                    </p>
                  )}

                  <div style={{
                    display: 'flex',
                    gap: '16px',
                    fontSize: 'var(--text-sm)',
                    color: 'var(--text-muted)',
                    marginTop: '8px'
                  }}>
                    {favorite.location?.average_rating && (
                      <span>
                        <i className="fa-solid fa-star" style={{ color: 'var(--star-filled)' }}></i>
                        {' '}{favorite.location.average_rating.toFixed(1)}
                      </span>
                    )}
                    {favorite.location?.review_count !== undefined && (
                      <span>
                        <i className="fa-solid fa-comment"></i>
                        {' '}{favorite.location.review_count} {favorite.location.review_count === 1 ? 'review' : 'reviews'}
                      </span>
                    )}
                  </div>

                  <p style={{
                    fontSize: 'var(--text-xs)',
                    color: 'var(--text-muted)',
                    marginTop: '8px'
                  }}>
                    Added {new Date(favorite.created_at).toLocaleDateString()}
                  </p>
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '8px 16px', fontSize: 'var(--text-sm)' }}
                    onClick={() => window.location.href = `/locations/${favorite.location?.id}`}
                  >
                    <i className="fa-solid fa-eye"></i>
                    View
                  </button>
                  <button
                    className="btn btn-secondary"
                    style={{ padding: '8px 12px', fontSize: 'var(--text-sm)' }}
                    onClick={() => handleRemoveFavorite(favorite.id, favorite.location?.name)}
                  >
                    <i className="fa-solid fa-trash"></i>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ProfilePage;
