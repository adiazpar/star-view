import {MAPBOX_CONFIG} from "./mapbox-config.js";
import {LocationService} from "./LocationService.js";
import {MapDebugger} from "./MapDebugger.js";

// Map controller class for drawing layers, user interaction:
export class MapController {
    constructor() {
        this.map = null;
        this.userInteracting = false;
        this.debugger = null;
        this.transitionDuration = 300;
        this.defaultZoom = MAPBOX_CONFIG.defaultZoom;

        this.activeInfoPanel = null;
        this.infoPanelVisible = false;

        // Existing constructor properties...
        this.selectedLocationId = null;  // Track currently selected location

        // Bind methods to preserve 'this' context
        this.handleLocationSelection = this.handleLocationSelection.bind(this);

        // Marker management:
        this.markerManager = {
            locations: new Map(),
            events: new Map(),
            data: new Map(),
        };

        // Filter state management:
        this.filters = {
            activeTab: 'all',
            eventTypes: new Set(),
            searchQuery: '',
            showFavorites: false,
            showMyLocations: false
        };

        // Pagination state:
        this.pagination = {
            currentPage: 1,
            itemsPerPage: 10,
            totalItems: 0,
        }

        // Load saved filters before DOM initialization:
        this.initialize();
    }


    // Map Functions: ------------------------------------------ //
    async initialize() {
        try {
            await this.initializeMap();
            await this.setupMapFeatures();

            // Initialize UI only after DOM is fully loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.initializeUI();
                });
            } else {
                // If DOM is already loaded, initialize UI immediately
                this.initializeUI();
            }

        } catch(error) {
            console.error('Map initialization failed: ', error);
        }
    }

    applyInitialState() {
        // Get all items
        const items = document.querySelectorAll('.location-item');

        // Set initial visibility
        items.forEach(item => {
            item.style.display = '';  // Make all items visible initially
        });

        // Calculate initial pagination
        this.pagination.totalItems = items.length;

        // Apply initial pagination
        this.updatePagination();

        // Update item visibility based on first page
        const startIndex = 0;
        const endIndex = this.pagination.itemsPerPage;

        items.forEach((item, index) => {
            item.style.display = (index >= startIndex && index < endIndex) ? '' : 'none';
        });
    }

    async initializeMap() {
        mapboxgl.accessToken = MAPBOX_CONFIG.accessToken;
        this.map = new mapboxgl.Map({
            container: 'map',
            projection: 'globe',
            style: MAPBOX_CONFIG.style,
            zoom: MAPBOX_CONFIG.defaultZoom,
            center: MAPBOX_CONFIG.defaultCenter,
        });

        return new Promise((resolve) => {
            this.map.on('load', () => {
                this.setupEventListeners();
                this.handleURLParameters();
                this.setupMapTerrain();
                resolve();
            });
        });
    }

    handleURLParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const lat = parseFloat(urlParams.get('lat'));
        const lng = parseFloat(urlParams.get('lng'));
        const zoom = parseFloat(urlParams.get('zoom')) || 12;

        if (lat && lng) {
            this.map.flyTo({
                center: [lng, lat],
                zoom: zoom,
                essential: true
            });
        }
    }

    setupMapTerrain() {
        this.map.setFog({
            'space-color': '#000000',
            'star-intensity': 1.0,
            'color': '#242B4B',
            'high-color': '#161B36',
            'horizon-blend': 0.05
        });


        this.map.addSource('mapbox-dem', {
            'type': 'raster-dem',
            'url': 'mapbox://mapbox.terrain-rgb',
            'tileSize': 512,
            'maxzoom': 14
        });


        this.map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
    }

    async setupMapFeatures() {
        this.setupFilters();
        this.setupMapControls();
        this.setupDarkSkyLayer();
        await this.loadLocationsAndEvents();

        const tileButton = document.getElementById('show-tile-borders');
        const gridButton = document.getElementById('show-pixel-grid');

        // If debugger is disabled, hide the buttons:
        if(!MAPBOX_CONFIG.debugEnabled) {
            tileButton.style.display = 'none';
            gridButton.style.display = 'none';
        }
        else {
            this.setupDebugger();
        }
    }

    setupEventListeners() {
        // Map interaction events:
        this.map.on('mousedown', () => this.userInteracting = true);
        this.map.on('dragstart', () => this.userInteracting = true);
        this.map.on('moveend', () => {
            this.userInteracting = false;
            this.updateMapMarkers();
        });

        this.map.on('zoomend', () => {
            // Update markers whenever the zoom level changes
            this.updateMapMarkers();
        });
    }

setupMapControls() {
    this.map.addControl(new mapboxgl.NavigationControl());

    this.map.addControl(new mapboxgl.GeolocateControl({
        positionOptions: { enableHighAccuracy: true },
        trackUserLocation: true,
        showUserHeading: true
    }));

    class OrbitControl { //adds go to orbit button
        onAdd(map) {
            this.map = map;
            this.container = document.createElement('div');
            this.container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group';
            const button = document.createElement('button');
            button.className = 'orbit-button';
            button.title = 'Go to Orbit';
            button.innerHTML = '🚀';

            button.addEventListener('click', () => {
                this.map.flyTo({
                    zoom: 0,
                    center: this.map.getCenter(),
                    speed: 1.2,
                });
            });
            this.container.appendChild(button);
            return this.container;
        }
        onRemove() {
            this.container.parentNode.removeChild(this.container);
            this.map = undefined;
        }
    }
    this.map.addControl(new OrbitControl(), 'top-right');
}


setupDarkSkyLayer() {
        // Add dark sky source and layer:
        this.map.addSource('dark-sky', {
            type: 'raster',
            tiles: ['/tiles/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: 'Dark Sky Data © NASA Earth Observatory',
            bounds: [-180, -85.0511, 180, 85.0511],
            minzoom: 0,
            maxzoom: 8
        });

        this.map.addLayer({
            id: 'dark-sky-layer',
            type: 'raster',
            source: 'dark-sky',
            layout: { 'visibility': 'none', },
            paint: {
                'raster-opacity': 0.7,
                'raster-fade-duration': 0
            }
        });


        // Set up click handler for existing button
        document.getElementById('toggle-dark-sky').addEventListener('click', () => {
            const visibility = this.map.getLayoutProperty('dark-sky-layer', 'visibility');
            const isVisible = visibility === 'visible';

            this.map.setLayoutProperty(
                'dark-sky-layer',
                'visibility',
                visibility === 'visible' ? 'none' : 'visible'
            );

            // Toggle button state
            document.getElementById('toggle-dark-sky').classList.toggle('active', !isVisible);

            // Toggle legend visibility
            document.querySelector('.legend').classList.toggle('visible', !isVisible);
        });
    }

    setupDebugger() {
        this.debugger = new MapDebugger(this.map);
        this.debugger.addDebugControls();
    }

    async loadLocationsAndEvents() {
        try {
            const [locations, events] = await Promise.all([
                LocationService.getViewingLocations(),
                LocationService.getCelestialEvents()
            ]);

            if (locations?.length) this.displayLocations(locations);
            if (events?.length) this.displayEvents(events);

        } catch (error) {
            console.error('Failed to load data: ', error);
        }
    }

    displayLocations(locations) {
        try {
            // Clear existing markers:
            this.markerManager.locations.forEach(marker => marker.remove());
            this.markerManager.locations.clear();

            // Store the full location data including favorites
            this.locations = locations.map(location => {
                const locationElement = document.querySelector(`.location-item[data-id="${location.id}"]`);
                return {
                    ...location,
                    is_favorited: locationElement ?
                        locationElement.getAttribute('is-favorite') === 'true' :
                        false
                };
            });

            locations.forEach(location => {
                // Create marker element
                const el = document.createElement('div');
                el.className = 'location-marker';

                // Create marker HTML
                el.innerHTML = `
                    <div class="marker-icon" style="background-color: var(--primary)">
                        <i class="fa-solid fa-location-dot"></i>
                    </div>
                `;

                // Create and add the marker
                const marker = new mapboxgl.Marker({
                    element: el,
                    anchor: 'bottom'
                })
                .setLngLat([location.longitude, location.latitude])
                .addTo(this.map);

                // Add click event listener to the marker element
                el.addEventListener('click', () => {
                    this.handleLocationSelection(location, el);
                });

                // Store marker reference
                this.markerManager.locations.set(location.id, marker);
            });

        } catch (error) {
            console.error('Error displaying locations:', error);
        }
    }

    displayEvents(events) {
        try {
            // Clear existing event markers:
            this.markerManager.events.forEach(marker => marker.remove());
            this.markerManager.events.clear();

            // Event type configurations
            const eventConfigs = {
                'METEOR': {
                    color: '#FF6B6B',
                    icon: '<i class="fas fa-meteor"></i>'
                },
                'ECLIPSE': {
                    color: '#4ECDC4',
                    icon: '<i class="fas fa-moon"></i>'
                },
                'PLANET': {
                    color: '#45B7D1',
                    icon: '<i class="fas fa-globe"></i>'
                },
                'AURORA': {
                    color: '#96CEB4',
                    icon: '<i class="fas fa-sparkles"></i>'
                },
                'COMET': {
                    color: '#F0ADFFFF',
                    icon: '<i class="fas fa-star"></i>'
                },
                'OTHER': {
                    color: '#CC00CC',
                    icon: '<i class="fas fa-star-shooting"></i>'
                }
            };

            events.forEach(event => {
                const el = document.createElement('div');
                el.className = 'event-marker';

                // Get event styling configuration, fallback to OTHER if type not found
                const config = eventConfigs[event.event_type] || eventConfigs['OTHER'];

                // Create marker HTML with event-specific icon
                el.innerHTML = `
                    <div class="event-marker-icon" style="background-color: ${config.color}">
                        ${config.icon}
                    </div>
                    <div class="event-marker-radius" style="border-color: ${config.color}"></div>
                `;

                // Create and add marker
                const marker = new mapboxgl.Marker({
                    element: el,
                    anchor: 'center'
                })
                .setLngLat([event.longitude, event.latitude]);

                marker.eventType = event.event_type;

                marker.addTo(this.map);

                // Click event for more details
                el.addEventListener('click', () => {
                    this.flyToLocation(event.latitude, event.longitude, 5000, 12, true);
                });

                this.markerManager.events.set(event.id, marker);
            });

        } catch (error) {
            console.error('Error displaying events:', error);
        }
    }


    // INFO Panel: --------------------------------------------- //
    async createInfoPanel(location) {

        // Get or create info panel container
        let infoPanel = document.querySelector('.location-info-panel');
        if (!infoPanel) {
            infoPanel = document.createElement('div');
            infoPanel.className = 'location-info-panel';
            document.querySelector('.map-view').appendChild(infoPanel);
        }

        // Format values with proper handling of unavailable data
        const cloudCover = location.cloudCoverPercentage >= 0
            ? `${location.cloudCoverPercentage}%`
            : 'Not available';

        const lightPollution = location.light_pollution_value
            ? `${location.light_pollution_value.toFixed(2)} mag/arcsec²`
            : 'Not available';

        const qualityScore = location.quality_score
            ? `${Math.round(location.quality_score)}/100`
            : 'Not available';

        // Calculate average rating - similar to your template filter
        const reviews = location.reviews || [];
        const averageRating = reviews.length > 0
            ? Math.round(reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length)
            : 0;

        // Generate star HTML - we'll create 5 stars, filled based on the average rating
        const starsHTML = Array.from({ length: 5 }, (_, i) => {
            return `<i class="fas fa-star ${i < averageRating ? '' : 'empty'}"></i>`;
        }).join('');

        // Get login status from global variable or data attribute
        const isLoggedIn = window.currentUser === true;

        if (isLoggedIn) {
            try {
                const response = await fetch(`/api/viewing-locations/${location.id}/favorite/`, {
                    method: 'GET',
                    credentials: 'same-origin'
                });

                const data = await response.json();
                location.is_favorited = data.is_favorited;
            } catch(error) {
                console.error('Error checking favorite status:', error);
                location.is_favorited = false; // Default to false if request fails
            }
        } else {
            location.is_favorited = false; // Default to false for logged out users
        }

        // Create the action buttons HTML conditionally (favorites)
        const actionButtonsHTML = isLoggedIn ? `
            <button class="action-button favorite-button ${location.is_favorited ? 'active' : ''}" 
                    onclick="window.mapController.toggleFavorite(${location.id})">
                <i class="fas fa-heart"></i>
                ${location.is_favorited ? 'Unfavorite' : 'Favorite'}
            </button>
        ` : `
            <div class="action-button disabled">
                <i class="fas fa-lock"></i>
                Must be logged in to favorite
            </div>
        `;

        // Update panel content
        infoPanel.innerHTML = `
            <div class="panel-header">
                <button class="close-panel">
                    <i class="fas fa-times"></i>
                </button>
                <h3>${location.name}</h3>
                <div class="location-type">VIEWING LOCATION</div>
            </div>
            
            <div class="panel-body">
                <div class="info-section">
                
                    <div class="info-row">
                        <div class="info-icon">
                            <i class="fas fa-star-half-alt"></i>
                        </div>
                        <div class="info-content">
                            <label>User Ratings</label>
                            <div class="rating-container">
                                <div class="star-rating">
                                    <div class="star-rating-stars">
                                        ${starsHTML}
                                    </div>
                                    <span class="rating-count">(${reviews.length})</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-icon">
                            <i class="fas fa-cloud"></i>
                        </div>
                        <div class="info-content">
                            <label>Cloud Cover</label>
                            <span class="${cloudCover === 'Not available' ? 'unavailable' : ''}">${cloudCover}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-icon">
                            <i class="fas fa-moon"></i>
                        </div>
                        <div class="info-content">
                            <label>Light Pollution</label>
                            <span class="${lightPollution === 'Not available' ? 'unavailable' : ''}">${lightPollution}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-icon">
                            <i class="fas fa-star"></i>
                        </div>
                        <div class="info-content">
                            <label>Quality Score</label>
                            <span class="${qualityScore === 'Not available' ? 'unavailable' : ''}">${qualityScore}</span>
                        </div>
                    </div>

                    <div class="info-row">
                        <div class="info-icon">
                            <i class="fas fa-mountain"></i>
                        </div>
                        <div class="info-content">
                            <label>Elevation</label>
                            <span>${location.elevation.toFixed(0)} m</span>
                        </div>
                    </div>
                </div>

                ${location.formatted_address ? `
                    <div class="info-section">
                        <h4>Location Details</h4>
                        <div class="info-row">
                            <div class="info-icon">
                                <i class="fas fa-map-marker-alt"></i>
                            </div>
                            <div class="info-content">
                                <span class="address">${location.formatted_address}</span>
                                <label>${location.longitude} , ${location.latitude}</label>
                            </div>
                        </div>
                    </div>
                ` : ''}               

                <div class="panel-actions">
                     ${actionButtonsHTML}
                    <a href="/location/${location.id}" class="action-button primary">
                        <i class="fas fa-info-circle"></i>
                        View Full Details
                    </a>
                </div>
            </div>
        `;

        // Add event listeners
        const closeButton = infoPanel.querySelector('.close-panel');
        closeButton.addEventListener('click', () => this.hideInfoPanel());

        // Show panel with animation
        infoPanel.classList.add('visible');
        this.infoPanelVisible = true;
        this.activeInfoPanel = infoPanel;
    }

    hideInfoPanel() {
        if (this.activeInfoPanel) {
            this.activeInfoPanel.classList.remove('visible');
            this.infoPanelVisible = false;
            this.selectedLocationId = null;
            this.clearActiveStates();
        }
    }

    async toggleFavorite(locationId) {
        try {
            const location = this.findLocationById(locationId);
            if (!location) return;

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;


            const action = location.is_favorited ? 'unfavorite' : 'favorite';
            const response = await fetch(`/api/viewing-locations/${locationId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                // Toggle the favorited state
                location.is_favorited = !location.is_favorited;

                // Update the favorite button
                const favoriteButton = document.querySelector('.favorite-button');
                if (favoriteButton) {
                    favoriteButton.classList.toggle('active', location.is_favorited);
                    favoriteButton.innerHTML = `
                        <i class="fas fa-heart"></i>
                        ${location.is_favorited ? 'Unfavorite' : 'Favorite'}
                    `;
                }

                // Update the card in the list if it exists
                const locationCard = document.querySelector(`.location-item[data-id="${locationId}"]`);
                if (locationCard) {
                    locationCard.setAttribute('is-favorite', location.is_favorited.toString());
                    // Update the heart indicator if it exists
                    const heartIndicator = locationCard.querySelector('.favorite-indicator');
                    if (heartIndicator) {
                        heartIndicator.classList.toggle('active', location.is_favorited);
                    }
                }
            }
            else {
                console.error('Server responded with:', response.status);
                const errorData = await response.json();
                console.error('Error details:', errorData);
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
        }
    }


    // Flying Shit: -------------------------------------------- //
    flyToLocation(latitude, longitude, duration = 5000, zoom = 12, forceMove = false) {
        // Validate coordinates
        if (!latitude || !longitude) {
            console.error('Invalid coordinates:', latitude, longitude);
            return;
        }

        // Don't fly if user is interacting
        if (this.userInteracting && !forceMove) {
            return;
        }

        // Ensure the map is initialized
        if (!this.map) {
            console.error('Map not initialized');
            return;
        }

        try {
            this.map.flyTo({
                center: [longitude, latitude],
                zoom: zoom,
                duration: duration,
                essential: true,
                curve: 1.42, // Add a smooth ease-out curve
                speed: 1.2, // Slightly faster than default
            });
        } catch (error) {
            console.error('Error flying to location:', error);
        }
    }

    // Set up the location card listeners to read click inputs
    setupLocationCardListeners() {
        // Get all location cards
        const locationCards = document.querySelectorAll('.location-item[data-type="location"]');

        locationCards.forEach(card => {
            // First, remove any existing click listeners
            const newCard = card.cloneNode(true);
            card.parentNode.replaceChild(newCard, card);

            newCard.addEventListener('click', (event) => {
                // Prevent event handling if clicking the favorite heart
                if (event.target.closest('.favorite-indicator')) {
                    return;
                }
                const locationId = newCard.getAttribute('data-id');
                const isFavorited = newCard.getAttribute('is-favorite') === 'true';

                const location = this.findLocationById(locationId);

                if (location) {
                    location.is_favorited = isFavorited;
                    this.handleLocationSelection(location, newCard);
                }
            });
        });
    }

    // Unified handler for both marker and card clicks
    handleLocationSelection(location, element = null) {
        // Update selected state
        if (this.selectedLocationId === location.id) {
            // If clicking the same location, toggle the panel
            this.hideInfoPanel();
            this.selectedLocationId = null;
            this.clearActiveStates();
        } else {
            // New location selected
            this.selectedLocationId = location.id;

            // If clicked from map (not from card)
            if (!element?.classList.contains('location-item')) {
                // Find which page the item is on
                const locationCard = document.querySelector(`.location-item[data-id="${location.id}"]`);
                if (locationCard) {
                    location.is_favorited = locationCard.getAttribute('is-favorite') === 'true';

                    const visibleItems = Array.from(document.querySelectorAll('.location-item'))
                        .filter(item => !item.classList.contains('hidden'));

                    const itemIndex = visibleItems.indexOf(locationCard);
                    const targetPage = Math.floor(itemIndex / this.pagination.itemsPerPage) + 1;

                    // Only change page if needed
                    if (targetPage !== this.pagination.currentPage) {
                        this.pagination.currentPage = targetPage;
                        this.applyFilters();
                    }

                    // Wait for DOM update then scroll
                    setTimeout(() => {
                        locationCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }, 100);
                }
            }

            this.createInfoPanel(location);
            this.updateActiveStates(location.id);

            // Fly to location on the map
            this.flyToLocation(location.latitude, location.longitude, 5000, 12, true);
        }
    }

     // Helper method to find location data by ID
    findLocationById(locationId) {
        // Convert locationId to string for comparison since HTML attributes are strings
        const id = locationId.toString();
        const location = this.locations.find(loc => loc.id.toString() === id);

        if (!location) {
            console.warn(`No location found with ID: ${id}`);
        }
        return location;
    }

    // Update visual states for active elements
    updateActiveStates(locationId) {
        // Clear previous active states
        this.clearActiveStates();

        // Update card active state
        const card = document.querySelector(`.location-item[data-id="${locationId}"]`);
        if (card) {
            card.classList.add('active');
        }

        // Update marker active state
        const marker = this.markerManager.locations.get(locationId);
        if (marker) {
            marker.getElement().classList.add('active');
        }
    }

    // Clear all active states
    clearActiveStates() {
        // Clear active cards
        document.querySelectorAll('.location-item.active')
            .forEach(card => card.classList.remove('active'));

        // Clear active markers
        this.markerManager.locations.forEach(marker => {
            marker.getElement().classList.remove('active');
        });
    }


    // Filtering: ---------------------------------------------- //
    initializeUI() {
        this.setupFilters();
        this.initializePagination();
        this.setupFilters();
        this.applyInitialState();
        this.setupLocationCardListeners();
        this.setupFilterToggle();
    }

    setupFilterToggle() {
        const filterToggle = document.getElementById('filter-toggle');
        const filterPanel = document.querySelector('.filter-panel');

        if (filterToggle && filterPanel) {
            filterToggle.addEventListener('click', () => {
                // Toggle active state on button
                filterToggle.classList.toggle('active');

                // Toggle filter panel visibility
                filterPanel.classList.toggle('visible');
            });
        }
    }

    setupFilters() {
        // Tab filtering
        const tabButtons = document.querySelectorAll('.panel-tab');
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                // Remove active class from all tabs
                tabButtons.forEach(tab => tab.classList.remove('active'));

                // Add active class to clicked tab
                button.classList.add('active');

                // Update active tab in our filter state
                this.filters.activeTab = button.getAttribute('data-tab').toLowerCase();

                // Reset to first page:
                this.pagination.currentPage = 1;

                // Apply filters:
                this.applyFilters();
            });
        });

        // Event type filtering
        const eventTypeButtons = document.querySelectorAll('.event-type-filter .filter-buttons button');
        eventTypeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const eventType = button.getAttribute('data-type');

                // Toggle button active state
                button.classList.toggle('active');

                // Update our filter state
                if (this.filters.eventTypes.has(eventType)) {
                    this.filters.eventTypes.delete(eventType);
                } else {
                    this.filters.eventTypes.add(eventType);
                }

                this.pagination.currentPage = 1;

                // Apply filters:
                this.applyFilters();
            });
        });

        // Location filtering
        const locationFilterButtons = document.querySelectorAll('.location-type-filter .filter-buttons button');
        locationFilterButtons.forEach(button => {
            button.addEventListener('click', () => {
                const filterType = button.getAttribute('data-filter');

                // Toggle button state
                button.classList.toggle('active');

                // Update filter state
                if (filterType === 'favorites') {
                    this.filters.showFavorites = !this.filters.showFavorites;
                } else if (filterType === 'my-locations') {
                    this.filters.showMyLocations = !this.filters.showMyLocations;
                }

                // Reset to first page
                this.pagination.currentPage = 1;

                // Apply filters
                this.applyFilters();
            });
        });

        // Search filtering
        const searchInput = document.querySelector('.search-container input');
        searchInput.addEventListener('input', (e) => {
            this.filters.searchQuery = e.target.value.toLowerCase();

            this.pagination.currentPage = 1;

            // Apply filters:
            this.applyFilters();
        });
    }

    applyFilters() {
        if(!this.filters) {
            console.error('Filters objects is not initialized');
            return;
        }

        // Get all location items:
        const items = document.querySelectorAll('.location-item');
        let visibleItems = [];

        items.forEach(item => {
            let isVisible = true;
            const itemType = item.getAttribute('data-type');
            const eventType = item.getAttribute('data-event-type');
            const isFavorite = item.getAttribute('data-is-favorite')?.toLowerCase() === 'true';
            const isUserLocation = item.getAttribute('data-added-by') === window.currentUserId;

            // Tab filtering
            if (this.filters.activeTab !== 'all' && itemType !== this.filters.activeTab) {
                isVisible = false;
            }

            // Event type filtering
            if (isVisible && this.filters.eventTypes.size > 0 && itemType === 'event') {
                isVisible = this.filters.eventTypes.has(eventType);
            }

            // Location filtering (only apply to location items)
            if (isVisible && itemType === 'location') {
                if (this.filters.showFavorites && !isFavorite) {
                    isVisible = false;
                }
                if (this.filters.showMyLocations && !isUserLocation) {
                    isVisible = false;
                }
            }

            // Search filtering
            if (isVisible && this.filters.searchQuery) {
                const title = item.querySelector('.location-title')?.textContent.toLowerCase() || '';
                const description = item.querySelector('.location-address, .event-description')?.textContent.toLowerCase() || '';
                isVisible = title.includes(this.filters.searchQuery) ||
                           description.includes(this.filters.searchQuery);
            }

            // Important: Set pointer-events based on visibility
            if (isVisible) {
                item.style.pointerEvents = 'auto';
                item.classList.remove('hidden');
                visibleItems.push(item);
            } else {
                item.style.pointerEvents = 'none';
                item.classList.add('hidden');
                item.style.display = 'none'; // Immediately hide non-visible items
            }
        });

        // Update pagination with visible items count
        this.pagination.totalItems = visibleItems.length;

        // Ensure current page is valid with new total
        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);
        if (this.pagination.currentPage > totalPages) {
            this.pagination.currentPage = Math.max(1, totalPages);
        }

        // Update pagination display
        this.updatePagination();

        // Update visible items based on current page
        this.updateItemVisibility(visibleItems);

        // Update marker visibility on the map
        this.updateMapMarkers();
    }

    updateMapMarkers() {
        // Instead of handling individual markers, let's handle all markers based on the active tab
        const activeTab = this.filters.activeTab;

        // Handle location markers
        this.markerManager.locations.forEach((marker, key) => {
            const element = marker.getElement();
            const coordinates = marker.getLngLat();

            // Project the point to screen coordinates
            const point = this.map.project(coordinates);
            const bounds = this.map.getContainer().getBoundingClientRect();
            const padding = 100;

            // Check if marker is within view
            const isInView = point.x >= -padding &&
                            point.x <= bounds.width + padding &&
                            point.y >= -padding &&
                            point.y <= bounds.height + padding;

            // Find corresponding location item to get its attributes
            const locationItem = document.querySelector(
                `.location-item[data-lat="${coordinates.lat}"][data-lng="${coordinates.lng}"]`
            );

            let shouldShow = (activeTab === 'all' || activeTab === 'location') && isInView;

            // If we found a matching item, apply our location filters
            if (shouldShow && locationItem) {
                const isFavorite = locationItem.getAttribute('data-is-favorite').toLowerCase() === 'true';
                const isUserLocation = locationItem.getAttribute('data-added-by') === window.currentUserId;

                // Apply the same filtering logic as in applyFilters
                if (this.filters.showFavorites) {
                    shouldShow = isFavorite;
                }
                if (this.filters.showMyLocations) {
                    shouldShow = isUserLocation;
                }
            }

            // Apply visibility with transition
            if (element) {
                element.style.transition = `opacity ${this.transitionDuration}ms ease-in-out`;
                element.style.opacity = shouldShow ? '1' : '0';

                if (!shouldShow) {
                    setTimeout(() => {
                        element.style.display = 'none';
                    }, this.transitionDuration);
                } else {
                    element.style.display = '';
                    element.offsetHeight; // Force reflow
                    element.style.opacity = '1';
                }
            }
        });

        // Handle event markers with the same logic
        this.markerManager.events.forEach((marker) => {
            const element = marker.getElement();
            const coordinates = marker.getLngLat();

            // Project the point to screen coordinates
            const point = this.map.project(coordinates);

            // Get the map's container dimensions
            const bounds = this.map.getContainer().getBoundingClientRect();

            // Check visibility using the same projection method
            const padding = 100;
            const isVisible = point.x >= -padding &&
                            point.x <= bounds.width + padding &&
                            point.y >= -padding &&
                            point.y <= bounds.height + padding;

            // Combine visibility with tab and event type filters
            let shouldShow = (activeTab === 'all' || activeTab === 'event') && isVisible;

            if (shouldShow && this.filters.eventTypes.size > 0) {
                shouldShow = this.filters.eventTypes.has(marker.eventType);
            }

            if (element) {
                element.style.transition = `opacity ${this.transitionDuration}ms ease-in-out`;
                element.style.opacity = shouldShow ? '1' : '0';

                if (!shouldShow) {
                    setTimeout(() => {
                        element.style.display = 'none';
                    }, this.transitionDuration);
                } else {
                    element.style.display = '';
                    element.offsetHeight; // Force reflow
                    element.style.opacity = '1';
                }
            }
        });
    }


    // Pagination: --------------------------------------------- //
    initializePagination() {
        // Ensure we have a pagination container
        let paginationContainer = document.querySelector('.pagination');
        if (!paginationContainer) {
            // If no pagination container exists, create one
            paginationContainer = document.createElement('div');
            paginationContainer.className = 'pagination';
            const locationList = document.querySelector('.location-list');
            if (locationList) {
                locationList.appendChild(paginationContainer);
            }
        }

        // Initial pagination update
        this.updatePagination();
    }

    updatePagination() {
        const paginationContainer = document.querySelector('.pagination');
        if (!paginationContainer) return;

        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);

        // Clear existing pagination
        paginationContainer.innerHTML = `
            <div class="pagination-prev"></div>
            <div class="page-numbers"></div>
            <div class="pagination-next"></div>
        `;

        // Only show pagination if we have more than one page
        if (totalPages <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }

        paginationContainer.style.display = 'flex';

        const prevContainer = paginationContainer.querySelector('.pagination-prev');
        const numbersContainer = paginationContainer.querySelector('.page-numbers');
        const nextContainer = paginationContainer.querySelector('.pagination-next');

        // Add prev button if not on first page
        if (this.pagination.currentPage > 1) {
            const prevButton = document.createElement('a');
            prevButton.className = 'page-item prev';
            prevButton.textContent = '←';
            prevButton.addEventListener('click', () => this.goToPage(this.pagination.currentPage - 1));
            prevContainer.appendChild(prevButton);
        }

        // Calculate visible page range
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.pagination.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // Adjust start page if needed
        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // Add first page and ellipsis if needed
        if (startPage > 1) {
            this.addPageButton(numbersContainer, 1);
            if (startPage > 2) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '...';
                numbersContainer.appendChild(ellipsis);
            }
        }

        // Add page numbers
        for (let i = startPage; i <= endPage; i++) {
            this.addPageButton(numbersContainer, i);
        }

        // Add last page and ellipsis if needed
        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                const ellipsis = document.createElement('span');
                ellipsis.className = 'page-ellipsis';
                ellipsis.textContent = '...';
                numbersContainer.appendChild(ellipsis);
            }
            this.addPageButton(numbersContainer, totalPages);
        }

        // Add next button if not on last page
        if (this.pagination.currentPage < totalPages) {
            const nextButton = document.createElement('a');
            nextButton.className = 'page-item next';
            nextButton.textContent = '→';
            nextButton.addEventListener('click', () => this.goToPage(this.pagination.currentPage + 1));
            nextContainer.appendChild(nextButton);
        }
    }

    addPageButton(container, pageNumber) {
        const button = document.createElement('a');
        button.className = `page-item${pageNumber === this.pagination.currentPage ? ' active' : ''}`;
        button.textContent = pageNumber;

        // Important: Use arrow function to preserve 'this' context
        button.addEventListener('click', () => {
            this.goToPage(pageNumber);
        });

        container.appendChild(button);
    }

    updateItemVisibility(visibleItems) {
        const startIndex = (this.pagination.currentPage - 1) * this.pagination.itemsPerPage;
        const endIndex = startIndex + this.pagination.itemsPerPage;

        // First hide all items
        visibleItems.forEach(item => {
            item.style.display = 'none';
        });

        // Then show only the items for the current page
        visibleItems.slice(startIndex, endIndex).forEach(item => {
            item.style.display = '';
            item.style.opacity = '1';
            item.style.pointerEvents = 'auto';
        });

        // Reattach listeners to visible cards
        //this.setupLocationCardListeners();
    }

    goToPage(pageNumber) {
        // Validate page number
        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);
        if (pageNumber < 1 || pageNumber > totalPages) return;

        // Update current page
        this.pagination.currentPage = pageNumber;

        // Get current visible items
        const visibleItems = Array.from(document.querySelectorAll('.location-item'))
            .filter(item => !item.classList.contains('hidden'));

        // Update pagination UI
        this.updatePagination();

        // Important: Update item visibility with the current visible items
        this.updateItemVisibility(visibleItems);
    }
}
