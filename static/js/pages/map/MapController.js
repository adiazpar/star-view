import {MAPBOX_CONFIG} from "./mapbox-config.js";
import {LocationService} from "./LocationService.js";

// Map controller class for drawing layers, user interaction:
export class MapController {
    constructor() {
        this.map = null;
        this.userInteracting = false;
        this.transitionDuration = 300;
        this.defaultZoom = MAPBOX_CONFIG.defaultZoom;

        this.activeInfoPanel = null;
        this.infoPanelVisible = false;
        
        // Initialize locations and events arrays to prevent undefined errors
        this.locations = [];
        this.events = [];

        // Track current login & Creation popups:
        this.currentLoginPopup = null;  // Track the current login popup
        this.currentCreationPopup = null;  // Track the current creation popup

        // Light pollution layer state
        this.lightPollutionVisible = true;


        // Existing constructor properties...
        this.selectedLocationId = null;  // Track currently selected location

        // Bind methods to preserve 'this' context
        this.handleLocationSelection = this.handleLocationSelection.bind(this);
        this.deleteLocation = this.deleteLocation.bind(this);

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
            // Setup UI elements immediately when DOM is ready (before map loads)
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.setupLocationCardListeners();
                    this.initializePagination();
                    this.applyInitialState();
                });
            } else {
                // If DOM is already loaded, setup immediately
                this.setupLocationCardListeners();
                this.initializePagination();
                this.applyInitialState();
            }

            await this.initializeMap();
            await this.setupMapFeatures();

            // Initialize remaining UI after map loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.initializeRemainingUI();
                });
            } else {
                this.initializeRemainingUI();
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

    // Advanced Filter Functions: ------------------------------------------ //
    async applyAdvancedFilters(filters) {
        try {
            console.log('Applying advanced filters:', filters);
            
            // Check if any advanced filters are actually applied
            const hasAdvancedFilters = Object.keys(filters).length > 0;
            
            if (!hasAdvancedFilters) {
                // No advanced filters, reload original data
                await this.loadLocationsAndEvents();
                return;
            }
            
            // Build API query parameters
            const queryParams = new URLSearchParams();
            
            Object.keys(filters).forEach(key => {
                if (filters[key] !== null && filters[key] !== undefined && filters[key] !== '') {
                    queryParams.append(key, filters[key]);
                }
            });
            
            // Fetch filtered locations
            const url = `/api/v1/viewing-locations/?${queryParams.toString()}`;
            const response = await fetch(url, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const locations = data.results || data;
            
            // Store that we're using filtered data
            this.isUsingAdvancedFilters = true;
            
            // Update markers on map
            this.updateMapMarkers(locations);
            
            // Update location list in sidebar  
            this.updateLocationList(locations);
            
            // Apply existing frontend filters on top of the API filtered results
            setTimeout(() => {
                this.applyFilters();
            }, 100);
            
            console.log(`Applied advanced filters, showing ${locations.length} locations`);
            
        } catch (error) {
            console.error('Error applying advanced filters:', error);
        }
    }

    async resetAdvancedFilters() {
        console.log('Resetting to original data');
        this.isUsingAdvancedFilters = false;
        await this.loadLocationsAndEvents();
        this.applyFilters(); // Apply any existing frontend filters
    }

    updateMapMarkers(locations) {
        // Clear existing location markers
        this.markerManager.locations.forEach(marker => marker.remove());
        this.markerManager.locations.clear();
        
        // Add new markers
        locations.forEach(location => {
            const marker = this.createLocationMarker(location);
            this.markerManager.locations.set(location.id, marker);
        });
    }

    createLocationMarker(location) {
        // Create marker element with category-based styling
        const el = document.createElement('div');
        el.className = 'map-marker location-marker';
        
        // Add category-specific styling if available
        if (location.category) {
            el.classList.add(`category-${location.category.slug}`);
            el.innerHTML = `<i class="${location.category.icon}"></i>`;
        } else {
            el.innerHTML = '<i class="fas fa-map-marker-alt"></i>';
        }
        
        // Add verification badge if verified
        if (location.is_verified) {
            el.classList.add('verified');
        }
        
        // Create popup content
        const popupContent = this.createLocationPopup(location);
        
        const popup = new mapboxgl.Popup({
            offset: 25,
            closeButton: true,
            closeOnClick: false
        }).setHTML(popupContent);
        
        // Create and add marker
        const marker = new mapboxgl.Marker(el)
            .setLngLat([location.longitude, location.latitude])
            .setPopup(popup)
            .addTo(this.map);
            
        // Add click handler
        el.addEventListener('click', () => {
            this.handleLocationSelection(location);
        });
        
        return marker;
    }

    createLocationPopup(location) {
        const verificationBadge = location.is_verified ? 
            '<span class="popup-verified"><i class="fas fa-check-circle"></i> Verified</span>' : '';
        
        const categoryInfo = location.category ? 
            `<div class="popup-category"><i class="${location.category.icon}"></i> ${location.category.name}</div>` : '';
        
        const qualityScore = location.quality_score ? 
            `<div class="popup-quality">Quality: ${location.quality_score.toFixed(1)}/100</div>` : '';
        
        return `
            <div class="location-popup">
                <h3>${location.name}</h3>
                ${verificationBadge}
                ${categoryInfo}
                ${qualityScore}
                <div class="popup-coordinates">${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}</div>
                <a href="/location/${location.id}/" class="popup-link">View Details</a>
            </div>
        `;
    }

    updateLocationList(locations) {
        const locationList = document.querySelector('.location-list');
        if (!locationList) return;
        
        // Clear existing items (keep only pagination)
        const existingItems = locationList.querySelectorAll('.location-item');
        existingItems.forEach(item => item.remove());
        
        // Add filtered locations
        locations.forEach(location => {
            const locationElement = this.createLocationListItem(location);
            locationList.insertBefore(locationElement, locationList.querySelector('.pagination'));
        });
        
        // Update pagination if needed
        this.updatePaginationForFiltered(locations.length);
    }

    createLocationListItem(location) {
        const div = document.createElement('div');
        div.className = 'location-item';
        div.setAttribute('data-lat', location.latitude);
        div.setAttribute('data-lng', location.longitude);
        div.setAttribute('data-type', 'location');
        div.setAttribute('data-id', location.id);
        div.setAttribute('data-is-favorite', location.is_favorited || 'false');
        div.setAttribute('data-added-by', location.added_by || '');
        
        const verificationBadge = location.is_verified ? 
            '<span class="verification-mini-badge"><i class="fas fa-check-circle"></i></span>' : '';
        
        const categoryIcon = location.category ? 
            `<i class="${location.category.icon}"></i>` : '<i class="fas fa-map-marker-alt"></i>';
        
        div.innerHTML = `
            <div class="item-snapshot">
                <div class="favorite-indicator">
                    <i class="fas fa-heart"></i>
                </div>
                <img class="location-map"
                     src="https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/${location.longitude},${location.latitude},6/150x150@2x?access_token=${mapboxgl.accessToken}&attribution=false"
                     alt="Map view of ${location.name}">
            </div>
            <div class="item-content">
                <h3 class="location-title">
                    ${location.name}
                    ${verificationBadge}
                </h3>
                <div class="location-type">
                    ${categoryIcon}
                    ${location.category ? location.category.name : 'Viewing Location'}
                </div>
                <div class="location-info">
                    <div class="star-rating">
                        <div class="star-rating-stars">
                            ${this.generateStarRating(location.average_rating || 0)}
                        </div>
                        <span class="star-rating-count">(${location.review_count || 0})</span>
                    </div>
                    <div class="info-item">
                        SEE DETAILS
                    </div>
                </div>
            </div>
        `;
        
        return div;
    }

    generateStarRating(rating) {
        let stars = '';
        for (let i = 1; i <= 5; i++) {
            const filled = i <= Math.round(rating) ? 'filled' : '';
            stars += `<i class="fas fa-star ${filled}"></i>`;
        }
        return stars;
    }

    updatePaginationForFiltered(totalItems) {
        this.pagination.totalItems = totalItems;
        this.updatePagination();
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

        await new Promise((resolve) => {
            this.map.on('load', () => {
                this.handleURLParameters();
                this.setupMapTerrain();
                resolve();
            });
        });

        // Setup event listeners after map is loaded:
        this.setupEventListeners();
    }

    async loadLightPollutionLayer() {
        try {
            console.log('Starting to load light pollution layer...');
            
            // Use the tile server URL configured by Django
            const tileServerUrl = window.TILE_SERVER_URL;
                
            console.log(`Fetching tilesets from: ${tileServerUrl}/api/tilesets`);
            
            const response = await fetch(`${tileServerUrl}/api/tilesets`);
            console.log(`Response status: ${response.status}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received tileset data:', data);
    
            // Fix: Use the correct response structure
            if (data && data.tilesets && data.tilesets.length > 0) {
                // Find a light pollution tileset
                const lightPollutionTileset = data.tilesets.find(tileset => 
                    tileset.id.includes('light') || 
                    tileset.id.includes('pollution') ||
                    tileset.name.toLowerCase().includes('light') ||
                    tileset.name.toLowerCase().includes('pollution')
                );
    
                if (lightPollutionTileset) {
                    console.log('Found light pollution tileset:', lightPollutionTileset);
                    
                    // Construct the tile URL - use the same base URL as the API call
                    const tileUrl = `${tileServerUrl}/tiles/${lightPollutionTileset.id}/{z}/{x}/{y}.png`;
                    console.log('Tile URL template:', tileUrl);
                    
                    // Check if the layer already exists and remove it
                    if (this.map.getLayer('light-pollution-layer')) {
                        console.log('Removing existing light pollution layer');
                        this.map.removeLayer('light-pollution-layer');
                    }
                    if (this.map.getSource('light-pollution')) {
                        console.log('Removing existing light pollution source');
                        this.map.removeSource('light-pollution');
                    }
                    
                    // Add the tile source
                    this.map.addSource('light-pollution', {
                        'type': 'raster',
                        'tiles': [tileUrl],
                        'tileSize': lightPollutionTileset.tileSize || 256,
                        'maxzoom': lightPollutionTileset.maxZoom || 12,
                        'minzoom': lightPollutionTileset.minZoom || 0,
                        'bounds': lightPollutionTileset.bounds || [-180, -90, 180, 90],
                        'scheme': 'xyz'
                    });
    
                    console.log('Added light pollution source with bounds:', lightPollutionTileset.bounds);
    
                    // Add the layer
                    this.map.addLayer({
                        'id': 'light-pollution-layer',
                        'type': 'raster',
                        'source': 'light-pollution',
                        'paint': {
                            'raster-opacity': 0.6,
                            'raster-fade-duration': 300,
                            'raster-resampling': 'nearest'  // Smooth interpolation
                        }
                    });
                    
                    console.log('Light pollution layer added successfully!');
                    
                    // Test if tiles are loading by adding load/error listeners
                    this.map.on('sourcedata', (e) => {
                        if (e.sourceId === 'light-pollution' && e.isSourceLoaded) {
                            console.log('Light pollution tiles are loading...');
                        }
                    });
                    
                    this.map.on('error', (e) => {
                        if (e.source && e.source.id === 'light-pollution') {
                            if (e.error && e.error.status === 404) {
                                // Silently ignore 404 errors for light pollution tiles
                                // This happens for areas outside the data bounds (like Antarctica)
                                e.preventDefault();
                            } else if (e.error && e.error.message && e.error.message.includes('Failed to load tile')) {
                                // Also ignore tile loading errors for light pollution layer
                                console.debug('Light pollution tile load failed, likely outside data bounds');
                                e.preventDefault();
                            }
                        }
                    });
                    
                } else {
                    console.warn('No light pollution tileset found in available tilesets');
                    console.log('Available tilesets:', data.tilesets.map(ts => ({id: ts.id, name: ts.name})));
                }
            } else {
                console.warn('No tilesets found in API response');
                console.log('Response data:', data);
            }
        } catch (error) {
            console.error('Failed to load light pollution layer:', error);
            console.error('Error details:', {
                message: error.message,
                stack: error.stack
            });
            
            // Try to provide helpful debugging information
            if (error.message.includes('fetch')) {
                console.error('This might be a CORS or network connectivity issue');
                console.error('Make sure the tile server is running and accessible');
            }
        }
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
            'tileSize': 256,
            'maxzoom': 14
        });


        this.map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
    }

    async setupMapFeatures() {
        this.setupFilters();
        this.setupMapControls();
        this.setupStyleSwitcher();
        await this.loadLocationsAndEvents();
        await this.loadLightPollutionLayer();

        // Debug functionality has been completely removed
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

        // Add right-click handler (context menu):
        this.map.on('contextmenu', (e) => {
            // Prevent default context menu
            e.preventDefault();

            // First, clean up any existing popups
            if (this.currentLoginPopup) {
                this.currentLoginPopup.remove();
                this.currentLoginPopup = null;
            }
            if (this.currentCreationPopup) {
                this.currentCreationPopup.remove();
                this.currentCreationPopup = null;
            }

            if (!window.currentUser) {
                // Show login required message
                this.currentLoginPopup = new mapboxgl.Popup({
                    closeButton: true,
                    closeOnClick: false,
                    className: 'login-required-popup'  // Add this class
                })
                .setLngLat(e.lngLat)
                .setHTML(`
                    <div>
                        <p style="margin-bottom: var(--space-md)">Please log in to create viewing locations</p>
                        <a href="/login" class="action-button">Log In</a>
                    </div>
                `)
                .addTo(this.map);
                return;
            }

            this.showLocationCreationPopup(e.lngLat);
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

    setupStyleSwitcher() {
        // Define available map styles
        const styles = [
            { id: 'standard', name: 'Standard', url: 'mapbox://styles/mapbox/standard' },
            { id: 'satellite', name: 'Satellite', url: 'mapbox://styles/mapbox/satellite-streets-v12' },
            { id: 'outdoors', name: 'Outdoors', url: 'mapbox://styles/mapbox/outdoors-v12' },
            { id: 'light', name: 'Light', url: 'mapbox://styles/mapbox/light-v11' },
            { id: 'dark', name: 'Dark', url: 'mapbox://styles/mapbox/dark-v11' }
        ];

        // Track current style
        this.currentStyleId = 'standard';

        // Create custom control class
        class StyleSwitcherControl {
            constructor(styles, mapController) {
                this.styles = styles;
                this.mapController = mapController;
            }

            onAdd(map) {
                this.map = map;
                this.container = document.createElement('div');
                this.container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group style-switcher-control';

                // Create the main button
                this.button = document.createElement('button');
                this.button.className = 'style-switcher-button';
                this.button.type = 'button';
                this.button.setAttribute('aria-label', 'Switch map style');
                this.button.innerHTML = '<i class="fas fa-layer-group"></i><span>Standard</span>';
                
                // Create the dropdown menu
                this.menu = document.createElement('div');
                this.menu.className = 'style-switcher-menu';
                this.menu.style.display = 'none';

                // Add style options to menu
                this.styles.forEach(style => {
                    const option = document.createElement('button');
                    option.className = 'style-switcher-option';
                    option.type = 'button';
                    option.textContent = style.name;
                    option.setAttribute('data-style-id', style.id);
                    
                    if (style.id === this.mapController.currentStyleId) {
                        option.classList.add('active');
                    }

                    option.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.selectStyle(style);
                    });

                    this.menu.appendChild(option);
                });

                // Toggle menu on button click
                this.button.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleMenu();
                });

                // Close menu when clicking outside
                document.addEventListener('click', () => {
                    this.menu.style.display = 'none';
                });

                this.container.appendChild(this.button);
                this.container.appendChild(this.menu);
                return this.container;
            }

            toggleMenu() {
                const isVisible = this.menu.style.display === 'block';
                this.menu.style.display = isVisible ? 'none' : 'block';
            }

            selectStyle(style) {
                // Update active state
                this.menu.querySelectorAll('.style-switcher-option').forEach(opt => {
                    opt.classList.remove('active');
                });
                this.menu.querySelector(`[data-style-id="${style.id}"]`).classList.add('active');

                // Update button text
                this.button.innerHTML = `<i class="fas fa-layer-group"></i><span>${style.name}</span>`;

                // Close menu
                this.menu.style.display = 'none';

                // Update current style
                this.mapController.currentStyleId = style.id;

                // Change map style
                this.map.setStyle(style.url);

                // Re-apply map features after style load
                this.map.once('style.load', () => {
                    // Re-setup terrain (only for non-satellite styles)
                    if (style.id !== 'satellite') {
                        // Check if terrain source already exists to avoid duplicate
                        if (!this.map.getSource('mapbox-dem')) {
                            this.mapController.setupMapTerrain();
                        } else {
                            // Re-apply existing terrain
                            this.map.setTerrain({ 'source': 'mapbox-dem', 'exaggeration': 1.5 });
                        }
                    } else {
                        this.map.setTerrain(null);
                    }

                    // Re-load light pollution layer and apply current visibility state
                    this.mapController.loadLightPollutionLayer().then(() => {
                        // Apply current visibility state after layer is loaded
                        if (this.mapController.map.getLayer('light-pollution-layer')) {
                            this.mapController.map.setLayoutProperty(
                                'light-pollution-layer', 
                                'visibility', 
                                this.mapController.lightPollutionVisible ? 'visible' : 'none'
                            );
                        }
                    });

                    // Re-display markers
                    if (this.mapController.locations?.length) {
                        this.mapController.displayLocations(this.mapController.locations);
                    }
                    if (this.mapController.events?.length) {
                        this.mapController.displayEvents(this.mapController.events);
                    }
                });
            }

            onRemove() {
                this.container.parentNode.removeChild(this.container);
                this.map = undefined;
            }
        }

        // Add the control to the map
        this.map.addControl(new StyleSwitcherControl(styles, this), 'top-left');
        
        // Add light pollution toggle control
        this.setupLightPollutionToggle();
        
        console.log('Style switcher initialized');
    }

    setupLightPollutionToggle() {
        // Create custom control class for light pollution toggle
        class LightPollutionToggleControl {
            constructor(mapController) {
                this.mapController = mapController;
            }

            onAdd(map) {
                this.map = map;
                this.container = document.createElement('div');
                this.container.className = 'mapboxgl-ctrl mapboxgl-ctrl-group light-pollution-toggle-control';

                // Create the toggle button
                this.button = document.createElement('button');
                this.button.className = 'light-pollution-toggle-button active';
                this.button.type = 'button';
                this.button.setAttribute('aria-label', 'Toggle light pollution layer');
                this.button.innerHTML = '<i class="fas fa-moon"></i>';
                this.button.title = 'Toggle Light Pollution Layer';

                // Add click handler
                this.button.addEventListener('click', () => {
                    this.mapController.toggleLightPollutionLayer();
                });

                this.container.appendChild(this.button);
                return this.container;
            }

            updateButtonState(isVisible) {
                if (isVisible) {
                    this.button.classList.add('active');
                    this.button.title = 'Hide Light Pollution Layer';
                } else {
                    this.button.classList.remove('active');
                    this.button.title = 'Show Light Pollution Layer';
                }
            }

            onRemove() {
                this.container.parentNode.removeChild(this.container);
                this.map = undefined;
            }
        }

        // Store reference to the control so we can update its state
        this.lightPollutionToggleControl = new LightPollutionToggleControl(this);
        this.map.addControl(this.lightPollutionToggleControl, 'top-left');
        
        console.log('Light pollution toggle initialized');
    }

    toggleLightPollutionLayer() {
        this.lightPollutionVisible = !this.lightPollutionVisible;
        
        // Update button state
        this.lightPollutionToggleControl.updateButtonState(this.lightPollutionVisible);
        
        // Toggle layer visibility
        if (this.map.getLayer('light-pollution-layer')) {
            this.map.setLayoutProperty(
                'light-pollution-layer', 
                'visibility', 
                this.lightPollutionVisible ? 'visible' : 'none'
            );
        }
        
        console.log(`Light pollution layer ${this.lightPollutionVisible ? 'shown' : 'hidden'}`);
    }

    async loadLocationsAndEvents() {
        try {
            const [locations, events] = await Promise.all([
                LocationService.getViewingLocations(),
                LocationService.getCelestialEvents()
            ]);

            console.log('Loaded locations:', locations);
            console.log('Loaded events:', events);

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

                // Determine if location is favorited
                const isFavorited = location.is_favorited;

                // Create marker HTML
                el.innerHTML = `
                    <div class="marker-icon" style="background-color: ${isFavorited ? 'var(--pink)' : 'var(--primary)'}">
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


    // Location Creation Popup: -------------------------------- //
    showLocationCreationPopup(lngLat) {
        const popupContent = document.createElement('div');
        popupContent.className = 'popup-content';
        popupContent.setAttribute('role', 'dialog');
        popupContent.setAttribute('aria-labelledby', 'location-creation-title');

        popupContent.innerHTML = `
            <div class="popup-header">
                <h4 id="location-creation-title">Create New Viewing Location</h4>
            </div>
            <form class="popup-form" onsubmit="return false;">
                <div class="popup-input-container">
                    <label for="new-location-name" class="visually-hidden">Location name</label>
                    <input type="text" 
                           id="new-location-name" 
                           class="popup-input"
                           placeholder="Enter location name"
                           required
                           autocomplete="off">
                </div>
                <button type="submit"
                        id="create-location-btn" 
                        class="popup-action-button">
                    <i class="fas fa-plus" aria-hidden="true"></i>
                    <span>Create Location</span>
                </button>
            </form>
        `;

        // Create and show popup with corrected accessibility
        this.currentCreationPopup = new mapboxgl.Popup({
            closeButton: true,
            closeOnClick: false,
            className: 'location-creation-popup',
            maxWidth: '300px'
        })
        .setLngLat(lngLat)
        .setDOMContent(popupContent)
        .addTo(this.map);

        // Add event listener for popup close
        this.currentCreationPopup.on('close', () => {
            this.currentCreationPopup = null;
        });

        // Set up form submission
        const form = popupContent.querySelector('.popup-form');
        const nameInput = popupContent.querySelector('#new-location-name');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const name = nameInput.value.trim();
            if (name) {
                this.createViewingLocation(name, lngLat);
                this.currentCreationPopup.remove();
            } else {
                nameInput.classList.add('error');
                nameInput.addEventListener('input', () => {
                    nameInput.classList.remove('error');
                }, { once: true });
            }
        });

        // Focus input after popup is shown
        nameInput.focus();
    }

    async createViewingLocation(name, lngLat) {
        try {
            // Show loading state with animated dots
            const loadingPopup = new mapboxgl.Popup({
                closeButton: false,
                closeOnClick: false,
                className: 'loading-popup'
            })
            .setLngLat(lngLat)
            .setHTML(`
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            `)
            .addTo(this.map);

            // Create location data
            const locationData = {
                name: name,
                latitude: lngLat.lat,
                longitude: lngLat.lng,
            };

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Send POST request
            const response = await fetch('/api/v1/viewing-locations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'Accept': 'application/json'  // Explicitly request JSON response
                },
                body: JSON.stringify(locationData),
                credentials: 'same-origin'
            });

            // Remove loading popup
            loadingPopup.remove();

            // Handle non-successful responses
            if (!response.ok) {
                const errorData = await response.json();
                const errorMessage = errorData.error || 'Failed to create location. Please try again.';

                // Show error popup with specific message
                const errorPopup = new mapboxgl.Popup({
                    closeButton: true,
                    closeOnClick: false,
                    className: 'message-popup error',
                    maxWidth: '300px'
                })
                .setLngLat(lngLat)
                .setHTML(`<p><i class="fas fa-exclamation-circle"></i> ${errorMessage}</p>`)
                .addTo(this.map);

                // Log detailed error for debugging
                console.error('Server response:', errorData);
                return;
            }

            const newLocation = await response.json();
            this.displayLocations([newLocation]);
            await this.refreshLocationsList();
            await this.loadLocationsAndEvents();

            // Show success message
            const successPopup = new mapboxgl.Popup({
                closeButton: false,
                closeOnClick: true,
                className: 'message-popup success'
            })
            .setLngLat(lngLat)
            .setHTML('<p><i class="fas fa-check-circle"></i> Location created successfully!</p>')
            .addTo(this.map);

            // Remove success message after 2 seconds
            setTimeout(() => successPopup.remove(), 2000);

        } catch (error) {
            console.error('Error creating location:', error);

            // Show user-friendly error message
            const errorPopup = new mapboxgl.Popup({
                closeButton: true,
                closeOnClick: false,
                className: 'message-popup error'
            })
            .setLngLat(lngLat)
            .setHTML(`
                <p><i class="fas fa-exclamation-circle"></i> Something went wrong while creating the location.</p>
                <p style="font-size: smaller; margin-top: 8px;">Please try again or contact support if the problem persists.</p>
            `)
            .addTo(this.map);
        }
    }

    async deleteLocation(locationId) {
        try {
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Show confirmation popup
            const location = this.findLocationById(locationId);
            const marker = this.markerManager.locations.get(locationId);
            const lngLat = marker.getLngLat();

            const popup = new mapboxgl.Popup({
                closeButton: true,
                closeOnClick: false,
                className: 'delete-confirmation-popup',
                maxWidth: '300px'
            })
            .setLngLat(lngLat)
            .setHTML(`
                <div class="popup-content">
                    <p>Are you sure you want to delete "${location.name}"?</p>
                    <p style="font-size: smaller; color: var(--text-tertiary);">This action cannot be undone.</p>
                    <div class="popup-actions">
                        <button class="cancel-delete">Cancel</button>
                        <button class="confirm-delete">Delete</button>
                    </div>
                </div>
            `)
            .addTo(this.map);

            // Add event listeners to popup buttons
            const popupContent = popup.getElement();
            popupContent.querySelector('.cancel-delete').addEventListener('click', () => {
                popup.remove();
            });

            popupContent.querySelector('.confirm-delete').addEventListener('click', async () => {
                popup.remove();

                // Show loading popup
                const loadingPopup = new mapboxgl.Popup({
                    closeButton: false,
                    closeOnClick: false,
                    className: 'loading-popup'
                })
                .setLngLat(lngLat)
                .setHTML(`
                    <div class="loading-dots">
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                        <div class="loading-dot"></div>
                    </div>
                `)
                .addTo(this.map);

                try {
                    const response = await fetch(`/api/v1/viewing-locations/${locationId}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': csrfToken
                        },
                        credentials: 'same-origin'
                    });

                    loadingPopup.remove();

                    if (!response.ok) {
                        throw new Error('Failed to delete location');
                    }

                    // Hide info panel
                    this.hideInfoPanel();

                    // Remove marker from map
                    this.markerManager.locations.get(locationId).remove();
                    this.markerManager.locations.delete(locationId);

                    // Refresh location list
                    await this.loadLocationsAndEvents();
                    await this.refreshLocationsList();

                    // Show success message
                    const successPopup = new mapboxgl.Popup({
                        closeButton: false,
                        closeOnClick: true,
                        className: 'message-popup success'
                    })
                    .setLngLat(lngLat)
                    .setHTML('<p><i class="fas fa-check-circle"></i> Location deleted successfully</p>')
                    .addTo(this.map);

                    setTimeout(() => successPopup.remove(), 2000);

                } catch (error) {
                    console.error('Error deleting location:', error);

                    const errorPopup = new mapboxgl.Popup({
                        closeButton: true,
                        closeOnClick: false,
                        className: 'message-popup error'
                    })
                    .setLngLat(lngLat)
                    .setHTML(`
                        <p><i class="fas fa-exclamation-circle"></i> Failed to delete location</p>
                        <p style="font-size: smaller; margin-top: 8px;">Please try again or contact support if the problem persists.</p>
                    `)
                    .addTo(this.map);
                }
            });

        } catch (error) {
            console.error('Error initiating delete:', error);
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

        // Generate stars HTML with the new 'filled' class system
        const starsHTML = Array.from({ length: 5 }, (_, i) => {
            return `<i class="fas fa-star ${i < averageRating ? 'filled' : ''}"></i>`;
        }).join('');

        // Get login status from global variable or data attribute
        const isLoggedIn = window.currentUser === true;
        const currentUserId = window.currentUserId?.toString();

        // Safely access the creator ID, accounting for possible undefined values
        const creatorId = location.added_by?.id?.toString();

        const showDeleteOption = isLoggedIn &&
                               currentUserId &&
                               creatorId &&
                               currentUserId === creatorId;

        if (isLoggedIn) {
            try {
                const response = await fetch(`/api/v1/viewing-locations/${location.id}/favorite/`, {
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
                ${showDeleteOption ? `
                    <button class="delete-panel" aria-label="Delete location">
                        <i class="fas fa-trash"></i>
                    </button>
                ` : ''}
                <button class="close-panel">
                    <i class="fas fa-times"></i>
                </button>
                <h3>${location.name}</h3>
                <div class="info-type">VIEWING LOCATION</div>
            </div>     
            
            <div class="info-tabs">
                <button class="info-tab active" data-tab="conditions">
                    <i class="fas fa-binoculars"></i>
                    Viewing Conditions
                </button>
                <button class="info-tab" data-tab="moon">
                    <i class="fas fa-moon"></i>
                    Moon Data
                </button>
            </div>

            <div class="panel-content-wrapper">
                <div class="tab-content-scroll">
                    <!-- Conditions Tab Content -->
                    <div class="tab-content active" data-tab="conditions">
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
                                    <span>${location.elevation ? location.elevation.toFixed(0) + ' m' : 'Not available'}</span>
                                </div>
                            </div>
                        </div>
                    
                    </div>
                    
                    <!-- Moon Data Tab Content -->
                    <div class="tab-content" data-tab="moon">
                        <div class="info-section">
                            <div class="info-row">
                                <div class="info-icon">
                                    <i class="fas fa-moon"></i>
                                </div>
                                <div class="info-content">
                                    <label>Moon Phase</label>
                                    <span>${location.moon_phase_info ? location.moon_phase_info.short_name : 'Unknown'}${location.moon_phase ? ' - ' + location.moon_phase.toFixed(1) + '%' : ''}</span>                                   
                                </div>
                            </div>
                            
                            <div class="info-row">
                                <div class="info-icon">
                                    <i class="fas fa-angle-up"></i>
                                </div>
                                <div class="info-content">
                                    <label>Moon Altitude</label>
                                    <span>${location.moon_altitude ? location.moon_altitude.toFixed(1) + '°' : 'Not available'}</span>
                                </div>
                            </div>
                            
                            <div class="info-row">
                                <div class="info-icon">
                                    <i class="fas fa-arrow-up"></i>
                                </div>
                                <div class="info-content">
                                    <label>Next Moonrise</label>
                                    <span>${location.next_moonrise ? new Date(location.next_moonrise).toLocaleTimeString() : 'Not available'}</span>
                                </div>
                            </div>
                            
                            <div class="info-row">
                                <div class="info-icon">
                                    <i class="fas fa-arrow-down"></i>
                                </div>
                                <div class="info-content">
                                    <label>Next Moonset</label>
                                    <span>${location.next_moonset ? new Date(location.next_moonset).toLocaleTimeString() : 'Not available'}</span>
                                </div>
                            </div>
                        </div>
                    </div>     
                </div>                                     
            </div>
            
            <div class="panel-bottom">
                <!-- Address Section -->              
                ${location.formatted_address ? `
                    <div class="location-details">
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
            
                
                <!-- Action buttons -->
                <div class="panel-actions">
                     ${actionButtonsHTML}
                    <a href="/location/${location.id}" class="action-button primary">
                        <i class="fas fa-info-circle"></i>
                        View Full Details
                    </a>                    
                </div>  
            </div>                
        `;

        // Tab switching functionality:
        const tabs = infoPanel.querySelectorAll('.info-tab');
        const tabContents = infoPanel.querySelectorAll('.tab-content');

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                // Remove active class from all tabs and contents
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));

                // Add active class to clicked tab and corresponding content
                tab.classList.add('active');
                const tabContent = infoPanel.querySelector(`.tab-content[data-tab="${tab.dataset.tab}"]`);
                tabContent.classList.add('active');
            });
        });

        // Delete button listener:
        if (showDeleteOption) {
            const deleteButton = infoPanel.querySelector('.delete-panel');
            if (deleteButton) {
                deleteButton.addEventListener('click', () => {
                    this.deleteLocation(location.id);
                });
            }
        }

        // Close button listeners
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
            // Check if user is authenticated
            const mapContainer = document.querySelector('.map-container');
            const isAuthenticated = mapContainer && mapContainer.dataset.currentUser === 'true';
            
            if (!isAuthenticated) {
                this.showErrorMessage('You must be logged in to favorite locations');
                return;
            }

            const location = this.findLocationById(locationId);
            if (!location) {
                this.showErrorMessage('Location not found');
                return;
            }

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
            if (!csrfToken) {
                this.showErrorMessage('Security token not found. Please refresh the page.');
                return;
            }


            const action = location.is_favorited ? 'unfavorite' : 'favorite';
            const response = await fetch(`/api/v1/viewing-locations/${locationId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken.value,
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

                // Update the marker color
                const marker = this.markerManager.locations.get(locationId);
                if (marker) {
                    const markerIcon = marker.getElement().querySelector('.marker-icon');
                    if (markerIcon) {
                        markerIcon.style.backgroundColor = location.is_favorited ? 'var(--pink)' : 'var(--primary)';
                    }
                    marker.getElement().setAttribute('data-favorited', location.is_favorited);
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
                let errorMessage = `HTTP ${response.status}`;
                try {
                    const errorData = await response.json();
                    console.error('Error details:', errorData);
                    errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}`;
                } catch (parseError) {
                    console.error('Could not parse error response:', parseError);
                }
                this.showErrorMessage(`Failed to ${action} location: ${errorMessage}`);
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            this.showErrorMessage(`Network error: ${error.message}`);
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

    // Set up the location card listeners using event delegation
    setupLocationCardListeners() {
        const locationList = document.querySelector('.location-list');
        if (!locationList) {
            console.warn('Location list container not found');
            return;
        }

        // Use event delegation - single listener on parent container
        locationList.addEventListener('click', (event) => {
            // Find the clicked location card (if any)
            const card = event.target.closest('.location-item[data-type="location"]');

            // If click wasn't on a location card, ignore it
            if (!card) return;

            // Prevent event handling if clicking the favorite heart
            if (event.target.closest('.favorite-indicator')) {
                return;
            }

            const locationId = card.getAttribute('data-id');
            const isFavorited = card.getAttribute('is-favorite') === 'true';

            const location = this.findLocationById(locationId);

            if (location) {
                location.is_favorited = isFavorited;
                this.handleLocationSelection(location, card);
            }
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
        
        // Check if locations array exists and has data
        if (!this.locations || this.locations.length === 0) {
            console.warn('No locations data available. Locations may still be loading.');
            return null;
        }
        
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

    // Refresh the location list:
    async refreshLocationsList() {
        try {
            // First, fetch the updated list of locations from the server
            const locationsList = document.querySelector('.location-list');
            const response = await fetch('/api/v1/viewing-locations/?page_size=100');
            const data = await response.json();
            
            // Handle paginated response
            const locations = data.results || data;

            // Clear existing items
            locationsList.innerHTML = '';

            // Add each location to the list
            locations.forEach(location => {
                const locationElement = document.createElement('div');
                locationElement.className = 'location-item';
                locationElement.setAttribute('data-type', 'location');
                locationElement.setAttribute('data-id', location.id);
                locationElement.setAttribute('data-lat', location.latitude);
                locationElement.setAttribute('data-lng', location.longitude);
                locationElement.setAttribute('is-favorite', location.is_favorited || false);
                locationElement.setAttribute('data-added-by', location.added_by.id);

                locationElement.innerHTML = `
                <div class="item-snapshot">
                    <div class="favorite-indicator ${location.is_favorited ? 'active' : ''}">
                        <i class="fas fa-heart"></i>
                    </div>
                    <img class="location-map" src="https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/${location.longitude},${location.latitude},3/150x150@2x?access_token=${MAPBOX_CONFIG.accessToken}&attribution=false" alt="Map view of ${location.name}">
                </div>
                <div class="item-content">
                    <h3 class="location-title">${location.name}</h3>
                    <div class="location-type">VIEWING LOCATION</div>
                    <div class="location-info">
                        <div class="star-rating">
                            <div class="star-rating-stars">
                                ${this.generateStarRating(location.reviews)}
                            </div>
                            <span class="star-rating-count">(${location.reviews?.length || 0})</span>
                        </div>
                        <div class="info-item">SEE DETAILS</div>
                    </div>
                </div>
            `;

                locationsList.appendChild(locationElement);
            });

            // Recalculate pagination
            this.pagination.totalItems = locations.length;
            this.pagination.currentPage = 1;  // Reset to first page

            // Apply filters and pagination
            this.applyFilters();

            // No need to reattach listeners - event delegation handles this

        } catch (error) {
            console.error('Error refreshing locations list:', error);
        }
    }

    // Helper method to generate star rating HTML
    generateStarRating(reviews) {
        const averageRating = reviews?.length > 0
            ? Math.round(reviews.reduce((sum, review) => sum + review.rating, 0) / reviews.length)
            : 0;

        return Array.from({ length: 5 }, (_, i) =>
            `<i class="fas fa-star ${i < averageRating ? '' : 'empty'}"></i>`
        ).join('');
    }

    // Filtering: ---------------------------------------------- //
    initializeRemainingUI() {
        // setupFilters() is already called in setupMapFeatures()
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
                const isFavorite = locationItem.getAttribute('data-is-favorite') === 'true';
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

    showErrorMessage(message) {
        // Remove any existing error messages first
        const existingErrors = document.querySelectorAll('.error-message');
        existingErrors.forEach(error => error.remove());

        // Create error message element
        const errorMessage = document.createElement('div');
        errorMessage.className = 'error-message';
        errorMessage.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            background: #dc3545;
            color: white;
            padding: 12px 16px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            max-width: 300px;
            font-size: 14px;
            transform: translateX(100%);
            transition: transform 0.3s ease-out;
        `;
        errorMessage.textContent = message;

        // Add to body
        document.body.appendChild(errorMessage);

        // Animate in
        setTimeout(() => {
            errorMessage.style.transform = 'translateX(0)';
        }, 10);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (errorMessage.parentNode) {
                errorMessage.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (errorMessage.parentNode) {
                        errorMessage.remove();
                    }
                }, 300);
            }
        }, 4000);
    }
}
