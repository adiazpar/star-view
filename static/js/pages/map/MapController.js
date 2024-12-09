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
        };

        // Pagination state:
        this.pagination = {
            currentPage: 1,
            itemsPerPage: 20,
            totalItems: 0,
        }

        // Load saved filters before DOM initialization:
        this.loadSavedFilters();
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
                    // Fly to the clicked location
                    this.flyToLocation(location.latitude, location.longitude, 5000, 12, true);
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

    setupLocationCardHovers() {
        const locationItems = document.querySelectorAll('.location-item');

        let isHovering = false;

        locationItems.forEach(item => {
            const lat = parseFloat(item.getAttribute('data-lat'));
            const lng = parseFloat(item.getAttribute('data-lng'));

            if (!isNaN(lat) && !isNaN(lng)) {
                let hoverTimeout;

                item.addEventListener('mouseenter', () => {
                    isHovering = true;
                    hoverTimeout = setTimeout(() => {
                        if (isHovering) {
                            this.flyToLocation(lat, lng);
                        }
                    }, 500);

                    item.classList.add('hover');
                });

                item.addEventListener('mouseleave', () => {
                    isHovering = false;
                    clearTimeout(hoverTimeout);
                    item.classList.remove('hover');

                    // Stop any ongoing camera animations
                    if (this.map) {
                        this.map.stop();
                    }
                });
            } else {
                console.warn('Invalid coordinates for item:', item);
            }
        });
    }


    // Filtering: ---------------------------------------------- //
    initializeUI() {
        this.setupFilters();
        this.initializePagination();
        this.setupFilters();
        this.setupLocationCardHovers();
        this.applyInitialState();
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
                this.saveFilters();
            });
        });

        // Event type filtering
        const eventTypeButtons = document.querySelectorAll('.event-type-filter button');
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
                this.saveFilters();
            });
        });

        // Search functionality
        const searchInput = document.querySelector('.search-container input');
        searchInput.addEventListener('input', (e) => {
            this.filters.searchQuery = e.target.value.toLowerCase();

            this.pagination.currentPage = 1;

            // Apply filters:
            this.applyFilters();
            this.saveFilters();
        });
    }

    applyFilters() {
        if(!this.filters) {
            console.error('Filters objects is not initialized');
            return;
        }

        const items = document.querySelectorAll('.location-item');
        let visibleCount = 0;

        items.forEach(item => {
            let isVisible = true;
            const itemType = item.getAttribute('data-type');
            const eventType = item.getAttribute('data-event-type');

            // Tab filtering
            if (this.filters.activeTab !== 'all') {
                isVisible = itemType === this.filters.activeTab;
            }

            // Event type filtering
            if (isVisible && this.filters.eventTypes.size > 0) {
                if (itemType === 'event') {
                    isVisible = this.filters.eventTypes.has(eventType);
                } else {
                    // If we're filtering by event types, hide all locations
                    isVisible = false;
                }
            }

            // Search filtering
            if (isVisible && this.filters.searchQuery) {
                const title = item.querySelector('.location-title')?.textContent.toLowerCase() || '';
                const description = item.querySelector('.location-address, .event-description')?.textContent.toLowerCase() || '';
                isVisible = title.includes(this.filters.searchQuery) || description.includes(this.filters.searchQuery);
            }

            // Update visibility
            if (isVisible) {
                item.classList.remove('hidden');
                visibleCount++;
            } else {
                item.classList.add('hidden');
            }
        });

        // Only update pagination if we have visible items
        if (visibleCount > 0) {
            this.pagination.totalItems = visibleCount;
            this.updatePagination();
        }

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

            // Get the map's container dimensions
            const bounds = this.map.getContainer().getBoundingClientRect();

            // A point is behind the globe if its projected x or y coordinates
            // are outside reasonable bounds (we add some padding to prevent flickering)
            const padding = 100;
            const isVisible = point.x >= -padding &&
                            point.x <= bounds.width + padding &&
                            point.y >= -padding &&
                            point.y <= bounds.height + padding;

            // Combine visibility check with tab filter
            const shouldShow = (activeTab === 'all' || activeTab === 'location') && isVisible;

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

        // Get actually visible items (those with display !== 'none')
        const visibleItems = Array.from(document.querySelectorAll('.location-item'))
            .filter(item => !item.classList.contains('hidden'));

        this.pagination.totalItems = visibleItems.length;
        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);

        // Create pagination structure
        const structure = `
            <div class="pagination-prev"></div>
            <div class="page-numbers"></div>
            <div class="pagination-next"></div>
        `;
        paginationContainer.innerHTML = structure;

        // Only show pagination if we have more than one page
        if (totalPages > 1) {
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

            // Add page numbers
            const maxVisiblePages = 5; // Adjust this number as needed
            let startPage = Math.max(1, this.pagination.currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

            // Adjust start page if we're near the end
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

            // Add visible page numbers
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

        // Update visibility of items based on current page
        this.updateItemVisibility(visibleItems);
    }

    addPageButton(container, pageNumber) {
        const button = document.createElement('a');
        button.className = `page-item${pageNumber === this.pagination.currentPage ? ' active' : ''}`;
        button.textContent = pageNumber;
        button.addEventListener('click', () => this.goToPage(pageNumber));
        container.appendChild(button);
    }

    updateItemVisibility(visibleItems) {
        const startIndex = (this.pagination.currentPage - 1) * this.pagination.itemsPerPage;
        const endIndex = startIndex + this.pagination.itemsPerPage;

        visibleItems.forEach((item, index) => {
            if (index >= startIndex && index < endIndex) {
                item.style.display = '';
                // Reset height for smooth transitions
                requestAnimationFrame(() => {
                    item.style.height = '';
                });
            } else {
                item.style.display = 'none';
            }
        });
    }

    goToPage(pageNumber) {
        // Ensure page number is valid
        const totalPages = Math.ceil(this.pagination.totalItems / this.pagination.itemsPerPage);
        if (pageNumber < 1 || pageNumber > totalPages) return;

        // Update current page
        this.pagination.currentPage = pageNumber;

        // Update pagination display
        this.updatePagination();
    }


    // Filter persistence: ------------------------------------- //
    saveFilters() {
        // Convert our filter state into a format suitable for storage
        const filterState = {
            activeTab: this.filters.activeTab,
            // Convert Set to Array for storage
            eventTypes: Array.from(this.filters.eventTypes),
            searchQuery: this.filters.searchQuery
        };

        // Save to localStorage with pretty formatting for debugging
        localStorage.setItem('mapFilters', JSON.stringify(filterState, null, 2));
    }

    loadSavedFilters() {
        try {
            // Attempt to load saved filters
            const savedFilters = localStorage.getItem('mapFilters');

            if (savedFilters) {
                const parsedFilters = JSON.parse(savedFilters);

                // Restore the filter state
                this.filters.activeTab = parsedFilters.activeTab || 'all';
                this.filters.eventTypes = new Set(parsedFilters.eventTypes || []);
                this.filters.searchQuery = parsedFilters.searchQuery || '';

                // Now we need to update the UI to match the loaded state
                this.restoreFilterUI();
            }
        } catch (error) {
            console.error('Error loading saved filters:', error);
            // If there's an error, we'll just use the default filters
        }
    }

    restoreFilterUI() {
        // Restore active tab
        const tabs = document.querySelectorAll('.panel-tab');
        tabs.forEach(tab => {
            const isActive = tab.getAttribute('data-tab') === this.filters.activeTab;
            tab.classList.toggle('active', isActive);
        });

        // Restore event type buttons
        const eventButtons = document.querySelectorAll('.event-type-btn');
        eventButtons.forEach(button => {
            const eventType = button.getAttribute('data-type');
            const isActive = this.filters.eventTypes.has(eventType);
            button.classList.toggle('active', isActive);
        });

        // Restore search query
        const searchInput = document.querySelector('.search-container input');
        if (searchInput) {
            searchInput.value = this.filters.searchQuery;
        }

        // Apply the restored filters
        this.applyFilters();
    }
}
