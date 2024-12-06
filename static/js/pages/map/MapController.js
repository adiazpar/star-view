import { MAPBOX_CONFIG } from "./mapbox-config.js";
import { LocationService } from "./LocationService.js";
import { MapDebugger, addLocation, addEvent, submitEventForm } from "./MapDebugger.js";

// Map controller class for drawing layers, user interaction:
export class MapController {
    constructor() {
        this.map = null;
        this.userInteracting = false;
        this.spinEnabled = true;
        this.secondsPerRevolution = MAPBOX_CONFIG.spinRevolutionTime;
        this.maxSpinZoom = MAPBOX_CONFIG.maxSpinZoom;
        this.debugger = null;

        // Marker management:
        this.markerManager = {
            locations: new Map(),
            events: new Map(),
            data: new Map(),
        };

        // Filter state management:
        this.filterState = {
            activeTab: 'all',
            activeFilters: new Set(),
            searchTerm: '',
        };
    }

    async initialize() {
        try {
            await this.initializeMap();
            await this.setupMapFeatures();

        } catch(error) {
            console.error('Map initialization failed: ', error);
        }
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
        this.initializeFilters();
        this.setupMapControls();
        this.setupDarkSkyLayer();
        await this.loadLocationsAndEvents();
        //this.setupDebugger()
    }

    setupEventListeners() {
        // Map interaction events:
        this.map.on('mousedown', () => this.userInteracting = true);
        this.map.on('dragstart', () => this.userInteracting = true);
        this.map.on('moveend', () => {
            this.userInteracting = false;
        });
    }

    setupMapControls() {
        this.map.addControl(new mapboxgl.NavigationControl());
        this.map.addControl(new mapboxgl.GeolocateControl({
            positionOptions: { enableHighAccuracy: true },
            trackUserLocation: true,
            showUserHeading: true
        }));
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


        // Add dark sky layer toggle button:
        const button = document.createElement('button');
        button.className = 'mapboxgl-ctrl-group mapboxgl-ctrl control';
        button.innerText = 'Toggle Dark Sky';
        button.onclick = () => {
            const visibility = this.map.getLayoutProperty('dark-sky-layer', 'visibility');
            this.map.setLayoutProperty(
                'dark-sky-layer',
                'visibility',
                visibility === 'visible' ? 'none' : 'visible'
            );
            // Update button state
            button.classList.toggle('active', visibility !== 'visible');
        };
        this.map.getContainer().appendChild(button);

        // Adding the legend:
        const legend = document.createElement('div');
        legend.className = 'mapboxgl-ctrl-group mapboxgl-ctrl legend';
        legend.innerHTML = `
            <h4>Dark Sky Levels</h4>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="background: linear-gradient(to right, black, floralwhite); width: 100px; height: 20px;"></div>
                <span style="margin-left: 10px;">Light Pollution Scale</span>
            </div>
        `;
        this.map.getContainer().appendChild(legend);
    }

    initializeFilters() {
        // Tab filtering:
        document.querySelectorAll('.panel-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                this.filterState.activeTab = tab.dataset.tab;
                this.updateFilters();
                this.updateTabStyles(tab);
            });
        });

        // Event type filtering
        document.querySelectorAll('.event-type-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;

                if (this.filterState.activeFilters.has(type)) {
                    this.filterState.activeFilters.delete(type);
                    btn.classList.remove('active');
                } else {
                    this.filterState.activeFilters.add(type);
                    btn.classList.add('active');
                }
                this.updateFilters();
            });
        });

        // Enhanced search
        const searchInput = document.getElementById('location-search');
        searchInput.addEventListener('input', (e) => {
            this.filterState.searchTerm = e.target.value.toLowerCase();
            this.updateFilters();
        });
    }

    updateTabStyles(activeTab) {
        document.querySelectorAll('.panel-tab').forEach(tab =>
            tab.classList.toggle('active', tab === activeTab));
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
                .setLngLat([event.longitude, event.latitude])
                .addTo(this.map);

                // Click event for more details
                el.addEventListener('click', () => {
                    // Fly to event location
                    this.map.flyTo({
                        center: [event.longitude, event.latitude],
                        zoom: 8,
                        essential: true
                    });
                });

                this.markerManager.events.set(event.id, marker);
            });

        } catch (error) {
            console.error('Error displaying events:', error);
        }
    }

    updateFilters() {
        document.querySelectorAll('.location-item').forEach(item => {
            const isVisible = this.checkItemVisibility(item);
            item.style.display = isVisible ? 'block' : 'none';
            this.updateMarkerVisibility(item, isVisible);
        });
    }

    checkItemVisibility(item) {
        if (this.filterState.activeTab !== 'all' &&
            item.dataset.type !== this.filterState.activeTab) {
            return false;
        }

        if (this.filterState.activeFilters.size > 0 &&
            item.dataset.type === 'event' &&
            !this.filterState.activeFilters.has(item.dataset.eventType)) {
            return false;
        }

        if (this.filterState.searchTerm) {
            const title = item.querySelector('.location-title').textContent.toLowerCase();
            const description = item.querySelector('.location-address, .event-description')
                ?.textContent.toLowerCase() || '';
            if (!title.includes(this.filterState.searchTerm) &&
                !description.includes(this.filterState.searchTerm)) {
                return false;
            }
        }

        return true;
    }

    updateMarkerVisibility(item, isVisible) {
        const lat = parseFloat(item.dataset.lat);
        const lng = parseFloat(item.dataset.lng);
        const markerKey = this.getMarkerKey(lat, lng);

        const marker = item.dataset.type === 'event'
            ? this.markerManager.events.get(markerKey)
            : this.markerManager.locations.get(markerKey);

        if (marker) {
            marker.getElement().style.display = isVisible ? 'block' : 'none';
        }
    }

    getMarkerKey(lat, lng) {
        return `${lat},${lng}`;
    }
}
