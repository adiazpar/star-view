import { useState, useEffect } from 'react';
import profileApi from '../../services/profile';
import Alert from '../Alert';
import CollapsibleSection from './CollapsibleSection';
import './ProfileSettings.css';

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

  // Password validation state (same as RegisterPage)
  const [passwordValidation, setPasswordValidation] = useState({
    minLength: false,
    hasUppercase: false,
    hasNumber: false,
    hasSpecial: false
  });

  // Confirm password validation state
  const [passwordMatch, setPasswordMatch] = useState(false);

  // Validate password in real-time
  const validatePassword = (password) => {
    setPasswordValidation({
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    });
  };

  // Validate password match
  const validatePasswordMatch = (newPassword, confirmPassword) => {
    setPasswordMatch(confirmPassword.length > 0 && newPassword === confirmPassword);
  };

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

    // Validate all password requirements are met
    if (!passwordValidation.minLength || !passwordValidation.hasUppercase ||
        !passwordValidation.hasNumber || !passwordValidation.hasSpecial) {
      setPasswordError('Please meet all password requirements');
      return;
    }

    // Validate passwords match
    if (!passwordMatch) {
      setPasswordError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await profileApi.updatePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setPasswordSuccess('Password updated successfully!');
      // Clear password fields and validation state
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      setPasswordValidation({
        minLength: false,
        hasUppercase: false,
        hasNumber: false,
        hasSpecial: false
      });
      setPasswordMatch(false);
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
    <CollapsibleSection title="Profile Settings" defaultExpanded={false}>
        <div className="profile-settings-grid">
        {/* Profile Picture Section */}
        <div className="profile-picture-section">
          <h3 className="profile-form-title">Profile Picture</h3>
          <p className="profile-form-description">Upload a photo to personalize your profile. This will be visible across the site.</p>

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
                <label htmlFor="profile-picture-input" className="btn">
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
                  className="btn"
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
          <h3 className="profile-form-title">Personal Information</h3>
          <p className="profile-form-description">Your name helps others recognize you. This will be displayed on your public profile.</p>

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

          <form onSubmit={handlePersonalInfoUpdate} className="profile-form">
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
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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
          <h3 className="profile-form-title">Username</h3>
          <p className="profile-form-description">3-30 characters. Letters, numbers, underscores, and hyphens only.</p>

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

          <form onSubmit={handleUsernameUpdate} className="profile-form">
            <div className="form-group">
              <input
                type="text"
                id="username"
                className="form-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={loading}
                placeholder="Enter username"
                aria-label="Username"
              />
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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
          <h3 className="profile-form-title">Email Address</h3>
          <p className="profile-form-description">For security, you'll need to verify your new email address before the change takes effect.</p>

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

          <form onSubmit={handleEmailUpdate} className="profile-form">
            <div className="form-group">
              <input
                type="email"
                id="email"
                className="form-input"
                value={personalInfo.email}
                onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                required
                disabled={loading}
                placeholder="your.email@example.com"
                aria-label="Email Address"
              />
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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
          <h3 className="profile-form-title">{user?.has_usable_password ? 'Change Password' : 'Set Password'}</h3>
          <p className="profile-form-description">
            {user?.has_usable_password
              ? 'Update your password to keep your account secure.'
              : 'Set a password to enable password-based login in addition to your social account.'
            }
          </p>
          {!user?.has_usable_password && (
            <p className="form-info">
              <i className="fa-solid fa-info-circle"></i> You currently sign in with a social account only.
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

          <form onSubmit={handlePasswordUpdate} className="profile-form">
            {/* Hidden username field for accessibility and password managers */}
            <input
              type="text"
              name="username"
              value={user?.username || ''}
              autoComplete="username"
              readOnly
              style={{ display: 'none' }}
              aria-hidden="true"
            />

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
                    placeholder="Enter your current password"
                    required
                    disabled={loading}
                    autoComplete="current-password"
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
                  onChange={(e) => {
                    const newPassword = e.target.value;
                    setPasswordData({ ...passwordData, new_password: newPassword });
                    validatePassword(newPassword);
                    validatePasswordMatch(newPassword, passwordData.confirm_password);
                  }}
                  placeholder="Create a password"
                  required
                  disabled={loading}
                  autoComplete="new-password"
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

              {/* Password Requirements (same as RegisterPage) */}
              <div className="password-requirements-list">
                <ul>
                  <li className={passwordValidation.minLength ? 'valid' : ''}>
                    <i className={`fa-solid ${passwordValidation.minLength ? 'fa-check' : 'fa-xmark'}`}></i>
                    At least 8 characters long
                  </li>
                  <li className={passwordValidation.hasUppercase ? 'valid' : ''}>
                    <i className={`fa-solid ${passwordValidation.hasUppercase ? 'fa-check' : 'fa-xmark'}`}></i>
                    At least 1 uppercase letter
                  </li>
                  <li className={passwordValidation.hasNumber ? 'valid' : ''}>
                    <i className={`fa-solid ${passwordValidation.hasNumber ? 'fa-check' : 'fa-xmark'}`}></i>
                    At least 1 number
                  </li>
                  <li className={passwordValidation.hasSpecial ? 'valid' : ''}>
                    <i className={`fa-solid ${passwordValidation.hasSpecial ? 'fa-check' : 'fa-xmark'}`}></i>
                    At least 1 special character (!@#$%^&*(),.?":{}|&lt;&gt;)
                  </li>
                </ul>
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
                  onChange={(e) => {
                    const confirmPassword = e.target.value;
                    setPasswordData({ ...passwordData, confirm_password: confirmPassword });
                    validatePasswordMatch(passwordData.new_password, confirmPassword);
                  }}
                  placeholder="Confirm your password"
                  required
                  disabled={loading}
                  autoComplete="new-password"
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

              {/* Password Match Requirement (same as RegisterPage) */}
              <div className="password-requirements-list">
                <ul>
                  <li className={passwordMatch ? 'valid' : ''}>
                    <i className={`fa-solid ${passwordMatch ? 'fa-check' : 'fa-xmark'}`}></i>
                    Passwords match
                  </li>
                </ul>
              </div>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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
          <h3 className="profile-form-title">Bio</h3>
          <p className="profile-form-description">Tell others about yourself. This will be visible on your public profile.</p>

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

          <form onSubmit={handleBioUpdate} className="profile-form">
            <div className="form-group">
              <div className="bio-textarea-wrapper">
                <textarea
                  id="bio"
                  className="form-textarea"
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows="4"
                  maxLength="150"
                  placeholder="Tell others about yourself..."
                  disabled={loading}
                  aria-label="Bio"
                />
                <span className="bio-character-count">{bio.length}/150</span>
              </div>
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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
          <h3 className="profile-form-title">Location</h3>
          <p className="profile-form-description">Where are you based? This will be visible on your public profile.</p>

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

          <form onSubmit={handleLocationUpdate} className="profile-form">
            <div className="form-group">
              <input
                type="text"
                id="location"
                className="form-input"
                value={locationField}
                onChange={(e) => setLocationField(e.target.value)}
                maxLength="100"
                placeholder="e.g., Seattle, WA"
                disabled={loading}
                aria-label="Location"
              />
            </div>
            <div className="profile-form-actions">
              <button type="submit" className="btn" disabled={loading}>
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

        </div>
      </CollapsibleSection>
  );
}

export default ProfileSettings;
