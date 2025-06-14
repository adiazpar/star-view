// API Service for handling all data fetching:
export class LocationService {
    static getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    static async getLocationStatus(locationId) {
        const response = await fetch(`/api/v1/viewing-locations/${locationId}/favorite/`, {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to get location status');
        return response.json();
    }

    static async toggleFavorite(locationID, currentlyFavorited) {
        const endpoint = currentlyFavorited ? 'unfavorite' : 'favorite';
        const response = await fetch(`/api/v1/viewing-locations/${locationID}/${endpoint}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error(`Failed to ${endpoint} location`);
        return response.json();
    }

    static async getViewingLocations() {
        // Request up to 100 locations (max allowed by the API)
        const response = await fetch('/api/v1/viewing-locations/?page_size=100', {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to fetch viewing locations');
        const data = await response.json();
        // Handle paginated response - return just the results array
        return data.results || data;
    }

    static async getCelestialEvents() {
        // Request up to 100 events (max allowed by the API)
        const response = await fetch('/api/v1/celestial-events/?page_size=100', {
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to fetch celestial events');
        const data = await response.json();
        // Handle paginated response - return just the results array
        return data.results || data;
    }
}