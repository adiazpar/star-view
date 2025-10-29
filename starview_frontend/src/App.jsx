/**
 * Main App Component
 *
 * This is a simple test to verify the React app can communicate
 * with the Django backend through the API.
 */

import { useState, useEffect } from 'react';
import locationsApi from './services/locations';

function App() {
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch locations when component mounts
  useEffect(() => {
    fetchLocations();
  }, []);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await locationsApi.getAll();
      console.log('API Response:', response.data);

      // Handle paginated response
      const locationsList = response.data.results || response.data;
      setLocations(locationsList);
    } catch (err) {
      console.error('Error fetching locations:', err);
      setError(err.message || 'Failed to fetch locations');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading locations...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h2 className="text-red-800 text-xl font-semibold mb-2">Error</h2>
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchLocations}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Starview</h1>
          <p className="text-gray-600">
            React + Django API Connection Test
          </p>
        </div>

        {/* Stats */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Locations</p>
              <p className="text-3xl font-bold text-blue-600">{locations.length}</p>
            </div>
            <div className="text-green-600">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">API connection successful!</p>
        </div>

        {/* Locations List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Locations</h2>

          {locations.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No locations found. Create one in the Django admin!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {locations.map((location) => (
                <div
                  key={location.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow"
                >
                  <h3 className="font-semibold text-lg text-gray-800 mb-2">
                    {location.name}
                  </h3>

                  {location.country && (
                    <p className="text-sm text-gray-600 mb-1">
                      {location.city && `${location.city}, `}
                      {location.state && `${location.state}, `}
                      {location.country}
                    </p>
                  )}

                  <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
                    <span>
                      {location.latitude?.toFixed(4)}, {location.longitude?.toFixed(4)}
                    </span>
                    {location.elevation && (
                      <span>{location.elevation}m</span>
                    )}
                  </div>

                  {location.average_rating && (
                    <div className="mt-2 flex items-center">
                      <span className="text-yellow-500">⭐</span>
                      <span className="ml-1 text-sm font-medium">
                        {location.average_rating.toFixed(1)}
                      </span>
                      {location.review_count > 0 && (
                        <span className="ml-1 text-sm text-gray-500">
                          ({location.review_count} reviews)
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-600 text-sm">
          <p>
            Backend API:{' '}
            <span className="font-mono bg-gray-200 px-2 py-1 rounded">
              http://localhost:8000/api
            </span>
          </p>
          <p className="mt-2">
            Frontend Dev Server:{' '}
            <span className="font-mono bg-gray-200 px-2 py-1 rounded">
              http://localhost:5173
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
