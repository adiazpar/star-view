/**
 * Map page initialization
 *
 * Initializes the MapController and sets up global configuration
 * by reading data attributes from the map container element.
 */

import { MapController } from './map_controller.js';

function initializePage() {
    // Initialize navbar if function exists
    if (typeof initNavbar === 'function') {
        initNavbar();
    }

    // Get user data from data attributes
    const mapContainer = document.querySelector('.map-container');
    if (!mapContainer) {
        console.error('Map container not found');
        return;
    }

    // Set global user context
    window.currentUser = mapContainer.dataset.currentUser === 'true';
    window.currentUserId = mapContainer.dataset.currentUserId || null;

    // Get tile server URL from data attribute
    window.TILE_SERVER_URL = mapContainer.dataset.tileServerUrl || '';

    // Debug logging
    console.log('🔧 Tile server URL configured as:', window.TILE_SERVER_URL);
    console.log('🌐 Current hostname:', window.location.hostname);
    console.log('🚀 Initializing map controller...');

    // Initialize the map controller
    window.mapController = new MapController();
    window.mapController.initialize();
}

// Initialize on next tick to ensure DOM is ready
setTimeout(initializePage, 0);
