import { Link } from 'react-router-dom';

function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <div className="page-container pt-8 pb-8">
        <div className="text-center">
          <h1 className="hero-title">
            Discover the Perfect
            <span className="hero-title-accent">
              Stargazing Spots
            </span>
          </h1>
          <p className="hero-text">
            Find and review the best locations for observing the night sky.
            Share your experiences with fellow astronomy enthusiasts.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/map" className="btn btn-lg">
              <i className="fa-solid fa-map"></i>
              <span className="icon-gap">Explore Map</span>
            </Link>
            <Link to="/register" className="btn btn-lg">
              <i className="fa-solid fa-user-plus"></i>
              <span className="icon-gap">Get Started</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="page-container pb-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="card">
            <i className="fa-solid fa-star feature-icon"></i>
            <h3 className="card-title">Rate Locations</h3>
            <p className="card-body">
              Share your experiences and help others find the best stargazing spots.
            </p>
          </div>
          <div className="card">
            <i className="fa-solid fa-map-location-dot feature-icon"></i>
            <h3 className="card-title">Interactive Map</h3>
            <p className="card-body">
              Browse locations on an interactive map with detailed information.
            </p>
          </div>
          <div className="card">
            <i className="fa-solid fa-comments feature-icon"></i>
            <h3 className="card-title">Community Reviews</h3>
            <p className="card-body">
              Read reviews and tips from experienced stargazers.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default HomePage;
