import { Link } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';

function Navbar() {
  // TODO: Get user authentication state from context/store
  const isAuthenticated = false;
  const { theme, toggleTheme } = useTheme();

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

        {/* Navigation Links */}
        <div className="navbar-nav">
          <button onClick={toggleTheme} className="btn-icon" aria-label="Toggle theme">
            <i className={theme === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon'}></i>
          </button>

          <Link to="/map" className="navbar-link">Map</Link>

          {isAuthenticated ? (
            <>
              <Link to="/account" className="navbar-link">Account</Link>
              <button
                onClick={() => {
                  // TODO: Implement logout
                  console.log('Logout clicked');
                }}
                className="navbar-link"
              >
                <span>Logout</span>
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="navbar-link">Login</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
