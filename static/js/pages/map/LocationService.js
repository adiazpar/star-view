// API Service for handling all data fetching:
export class LocationService {
    static getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    static async getLocationStatus(locationId) {
        const response = await fetch(`/api/viewing-locations/${locationId}/favorite/`, {
            headers: {
                'Content-Type': 'applications/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error('Failed to get location status');
        return response.json();
    }

    static async toggleFavorite(locationID, currentlyFavorited) {
        const endpoint = currentlyFavorited ? 'unfavorite' : 'favorite';
        const response = await fetch(`/api/viewing-locations/${locationID}/${endpoint}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'applications/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error(`Failed to ${endpoint} location`);
        return response.json();
    }

    static async getViewingLocations() {
        const response = await fetch('/api/viewing-locations/', {
            headers: {
                'Content-Type': 'applications/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error('Failed to fetch viewing locations');
        return response.json();
    }

    static async getCelestialEvents() {
        const response = await fetch('/api/celestial-events/', {
            headers: {
                'Content-Type': 'applications/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        });
        if (!response.ok) throw new Error('Failed to fetch celestial events');
        return response.json();
    }
}