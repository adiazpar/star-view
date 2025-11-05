import { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import authApi from '../services/auth';

function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Get the redirect URL from query params (e.g., /login?next=/profile)
  const nextUrl = searchParams.get('next') || '/';

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.login({
        username: formData.username,
        password: formData.password,
        next: nextUrl
      });

      // Login successful - redirect to specified URL
      const redirectUrl = response.data.redirect_url || nextUrl;
      window.location.href = redirectUrl;
    } catch (err) {
      // Handle different error scenarios
      if (err.response?.data?.message) {
        setError(err.response.data.message);
      } else if (err.response?.status === 401) {
        setError('Invalid username or password.');
      } else if (err.response?.status === 403) {
        setError('Account temporarily locked. Please try again later.');
      } else if (err.response?.status === 429) {
        setError('Too many login attempts. Please try again later.');
      } else {
        setError('Unable to login. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container pt-8 pb-8">
      {/* Centered container with max width */}
      <div style={{ maxWidth: '480px', margin: '0 auto', padding: '0 16px' }}>
        <div className="card">
          {/* Header */}
          <div className="card-header text-center">
            <h1 className="card-title" style={{ fontSize: '28px', marginBottom: '8px' }}>
              Welcome Back
            </h1>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '0' }}>
              Sign in to your Starview account
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="card-body">
            {/* Error Message */}
            {error && (
              <div className="alert alert-error" style={{ marginBottom: '16px' }}>
                <i className="alert-icon fa-solid fa-circle-exclamation"></i>
                <div className="alert-content">
                  <p className="alert-message">{error}</p>
                </div>
              </div>
            )}

            {/* Username/Email Field */}
            <div className="form-group">
              <label htmlFor="username" className="form-label">
                Username or Email
              </label>
              <input
                type="text"
                id="username"
                name="username"
                className="form-input"
                placeholder="Enter your username or email"
                value={formData.username}
                onChange={handleChange}
                required
                autoComplete="username"
                disabled={loading}
              />
            </div>

            {/* Password Field */}
            <div className="form-group">
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                className="form-input"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
                required
                autoComplete="current-password"
                disabled={loading}
              />
            </div>

            {/* Forgot Password Link */}
            <div className="text-right" style={{ marginBottom: '16px' }}>
              <Link
                to="/password-reset"
                style={{
                  color: 'var(--text-secondary)',
                  textDecoration: 'none',
                  fontSize: '14px'
                }}
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? (
                <>
                  <i className="fa-solid fa-spinner fa-spin"></i>
                  <span>Signing in...</span>
                </>
              ) : (
                <>
                  <i className="fa-solid fa-arrow-right-to-bracket"></i>
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="card-footer text-center">
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: '0' }}>
              Don't have an account?{' '}
              <Link
                to="/register"
                style={{
                  color: 'var(--accent)',
                  textDecoration: 'none',
                  fontWeight: '500'
                }}
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
