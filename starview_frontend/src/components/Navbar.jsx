import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useTheme } from '../hooks/useTheme';
import { useAuth } from '../hooks/useAuth';

function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const { isAuthenticated, user, loading, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [backdropVisible, setBackdropVisible] = useState(false);
  const [backdropClosing, setBackdropClosing] = useState(false);

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  // Handle backdrop visibility with delay for fade-out animation
  useEffect(() => {
    if (mobileMenuOpen) {
      // Show backdrop immediately when opening
      setBackdropVisible(true);
      setBackdropClosing(false);
    } else if (backdropVisible) {
      // Start closing animation
      setBackdropClosing(true);
      // When closing, wait for animation to finish before hiding
      const timer = setTimeout(() => {
        setBackdropVisible(false);
        setBackdropClosing(false);
      }, 300); // Match animation duration
      return () => clearTimeout(timer);
    }
  }, [mobileMenuOpen, backdropVisible]);

  return (
    <nav className="navbar">
      <div className="navbar-container">

        {/* Logo */}
        <Link to="/" className="navbar-logo">
          <img
            src={theme === 'dark' ? '/images/logo-dark.png' : '/images/logo-light.png'}
            alt="Starview Logo"
            className="logo-size"
          />
        </Link>

        {/* Desktop Navigation Links */}
        <div className="navbar-nav">
          <Link to="/" className="navbar-link">Home</Link>
          <Link to="/map" className="navbar-link">Map</Link>
          <Link to="/explore" className="navbar-link">Explore</Link>

          {isAuthenticated ? (
            // Authenticated: Show Profile and Logout
            <>
              <Link to="/profile" className="navbar-link">Profile</Link>
              <button onClick={logout} className="navbar-link login-btn">
                <i className="fa-solid fa-arrow-right-from-bracket"></i>
                Logout
              </button>
            </>
          ) : (
            // Not authenticated: Show Register and Login
            <>
              <Link to="/register" className="navbar-link">Register</Link>
              <Link to="/login" className="navbar-link login-btn">
                <i className="fa-solid fa-arrow-right-to-bracket"></i>
                Login
              </Link>
            </>
          )}
        </div>

        {/* Hamburger Button */}
        <button
          className="navbar-hamburger"
          onClick={toggleMobileMenu}
          aria-label="Toggle menu"
        >
          <i className={mobileMenuOpen ? "fa-solid fa-xmark" : "fa-solid fa-bars"}></i>
        </button>

        {/* Mobile Menu */}
        <div className={`navbar-mobile-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <Link to="/" className="navbar-mobile-link" onClick={closeMobileMenu}>
            <i className="fa-regular fa-house"></i>
            Home
          </Link>
          <Link to="/map" className="navbar-mobile-link" onClick={closeMobileMenu}>
            <i className="fa-solid fa-earth-europe"></i>
            Map
          </Link>
          <Link to="/explore" className="navbar-mobile-link" onClick={closeMobileMenu}>
            <i className="fa-solid fa-magnifying-glass"></i>
            Explore
          </Link>

          {isAuthenticated ? (
            // Authenticated: Show Profile and Logout
            <>
              <Link to="/profile" className="navbar-mobile-link" onClick={closeMobileMenu}>
                <i className="fa-regular fa-user"></i>
                Profile
              </Link>
              <button
                onClick={() => {
                  closeMobileMenu();
                  logout();
                }}
                className="navbar-mobile-link"
              >
                <i className="fa-solid fa-arrow-right-from-bracket"></i>
                Logout
              </button>
            </>
          ) : (
            // Not authenticated: Show Register and Login
            <>
              <Link to="/register" className="navbar-mobile-link" onClick={closeMobileMenu}>
                <i className="fa-regular fa-user"></i>
                Register
              </Link>
              <Link to="/login" className="navbar-mobile-link" onClick={closeMobileMenu}>
                <i className="fa-solid fa-arrow-right-to-bracket"></i>
                Login
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Backdrop */}
        {backdropVisible && (
          <div
            className={`navbar-mobile-backdrop ${backdropClosing ? 'closing' : ''}`}
            onClick={closeMobileMenu}
          ></div>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
