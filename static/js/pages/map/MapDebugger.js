// Class for debugging map features:
export class MapDebugger {
    constructor(map) {
        this.map = map;
        this.tileDebugEnabled = false;
        this.pixelDebugEnabled = false;
        this.currentTileLayer = null;
        this.updateTimeout = null;

        this.selectedTile = null;

        // Add throttled update on move
        this.map.on('move', () => {
            if (!this.updateTimeout) {
                this.updateTimeout = setTimeout(() => {
                    this.updateTileGrid();
                    if (this.pixelDebugEnabled) {
                        this.updatePixelGrid();
                    }
                    this.updateTimeout = null;
                }, 16); // Approximately 60fps (1000ms / 60)
            }
        });

        // Final update when movement ends
        this.map.on('moveend', () => {
            if (this.updateTimeout) {
                clearTimeout(this.updateTimeout);
                this.updateTimeout = null;
            }
            this.updateTileGrid();
        });
    }

    // TILE DEBUG FUNCTIONS: ---------------------------- //

    toggleTileDebug() {
        if (this.tileDebugEnabled) {
            // Remove existing tile debug layers
            if (this.map.getLayer('tile-debug-grid')) {
                this.map.removeLayer('tile-debug-grid');
            }
            if (this.map.getSource('tile-debug-source')) {
                this.map.removeSource('tile-debug-source');
            }
            this.tileDebugEnabled = false;
        } else {
            // Create a grid source for the current zoom level
            const zoom = Math.floor(this.map.getZoom());
            const bounds = this.map.getBounds();

            // Calculate tile boundaries
            const gridFeatures = this.createTileGrid(
                bounds.getWest(),
                bounds.getSouth(),
                bounds.getEast(),
                bounds.getNorth(),
                zoom
            );

            // Add source and layer for tile grid
            this.map.addSource('tile-debug-source', {
                'type': 'geojson',
                'data': {
                    'type': 'FeatureCollection',
                    'features': gridFeatures
                }
            });

            this.map.addLayer({
                'id': 'tile-debug-grid',
                'type': 'line',
                'source': 'tile-debug-source',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#FF0000',
                    'line-width': 2,
                    'line-opacity': 1
                }
            });

            this.tileDebugEnabled = true;
        }
    }

    createTileGrid(west, south, east, north, zoom) {
        const features = [];

        // Add bounds limiting to prevent pole issues
        south = Math.max(south, -85.0511); // Limit south to prevent projection issues
        north = Math.min(north, 85.0511);  // Limit north to prevent projection issues

        // Calculate tile ranges with safety checks
        const n = Math.pow(2, zoom);
        const west_tile = Math.floor((west + 180) / 360 * n);
        const east_tile = Math.ceil((east + 180) / 360 * n);

        // Add safety checks for latitude calculations
        const south_lat_rad = Math.max(-85.0511 * Math.PI / 180, south * Math.PI / 180);
        const north_lat_rad = Math.min(85.0511 * Math.PI / 180, north * Math.PI / 180);

        const south_tile = Math.floor((1 - Math.log(Math.tan(south_lat_rad) + 1 / Math.cos(south_lat_rad)) / Math.PI) / 2 * n);
        const north_tile = Math.ceil((1 - Math.log(Math.tan(north_lat_rad) + 1 / Math.cos(north_lat_rad)) / Math.PI) / 2 * n);

        // Add limit to number of tiles to prevent excessive calculations
        const MAX_TILES = 1000; // Arbitrary limit to prevent browser crashes
        const tile_count = (east_tile - west_tile) * (south_tile - north_tile);

        if (tile_count > MAX_TILES) {
            console.warn('Too many tiles to display, zoom in for more detail');
            return features;
        }

        try {
            // Create vertical lines (longitude boundaries)
            for (let x = west_tile; x <= east_tile; x++) {
                const lon = x * 360 / n - 180;
                features.push({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'LineString',
                        'coordinates': [
                            [lon, Math.max(-85.0511, south)],
                            [lon, Math.min(85.0511, north)]
                        ]
                    },
                    'properties': {
                        'type': 'vertical'
                    }
                });
            }

            // Create horizontal lines (latitude boundaries)
            for (let y = north_tile; y <= south_tile; y++) {
                // Add safety check for latitude calculation
                try {
                    const lat = Math.atan(Math.sinh(Math.PI * (1 - 2 * y / n))) * 180 / Math.PI;
                    if (lat >= -85.0511 && lat <= 85.0511) {  // Only add if within safe bounds
                        features.push({
                            'type': 'Feature',
                            'geometry': {
                                'type': 'LineString',
                                'coordinates': [
                                    [west, lat],
                                    [east, lat]
                                ]
                            },
                            'properties': {
                                'type': 'horizontal'
                            }
                        });
                    }
                } catch (e) {
                    console.warn('Skipping invalid latitude calculation');
                }
            }
        } catch (e) {
            console.error('Error creating tile grid:', e);
            return [];  // Return empty features on error
        }

        return features;
    }

    updateTileGrid() {
        if (this.tileDebugEnabled) {
            try {
                const bounds = this.map.getBounds();
                const zoom = Math.floor(this.map.getZoom());

                // Check if we're too close to poles
                if (bounds.getNorth() > 85.0511 || bounds.getSouth() < -85.0511) {
                    console.warn('Too close to poles, tile debug may be inaccurate');
                    return;  // Optionally return to prevent updates near poles
                }

                const gridFeatures = this.createTileGrid(
                    bounds.getWest(),
                    bounds.getSouth(),
                    bounds.getEast(),
                    bounds.getNorth(),
                    zoom
                );

                const source = this.map.getSource('tile-debug-source');
                if (source) {
                    source.setData({
                        'type': 'FeatureCollection',
                        'features': gridFeatures
                    });
                }
            } catch (e) {
                console.error('Error updating tile grid:', e);
                // Optionally disable tile debug if there's an error
                this.tileDebugEnabled = false;
            }
        }
    }

    // PIXEL DEBUG FUNCTIONS: --------------------------- //

    createPixelGrid(west, south, east, north, zoom) {
        const features = [];
        const tileSize = 256; // Standard tile size

        if(!this.selectedTile) {
            return features;
        }

        // Only create pixel grid for the selected tile:
        const { x: x_tile, y: y_tile } = this.selectedTile;

        // Calculate bounds for just this tile
        const n = Math.pow(2, zoom);
        const tile_west = x_tile * 360 / n - 180;
        const tile_east = (x_tile + 1) * 360 / n - 180;
        const tile_north = Math.atan(Math.sinh(Math.PI * (1 - 2 * y_tile / n))) * 180 / Math.PI;
        const tile_south = Math.atan(Math.sinh(Math.PI * (1 - 2 * (y_tile + 1) / n))) * 180 / Math.PI;

        // Only show pixel grid when zoomed in enough
        if (zoom < 8) {
            console.warn('Zoom in to see pixel grid');
            return features;
        }

        // Create grid for each pixel in the selected tile
        for (let px = 0; px < tileSize; px++) {
            for (let py = 0; py < tileSize; py++) {
                const pixel_west = tile_west + (tile_east - tile_west) * px / tileSize;
                const pixel_east = tile_west + (tile_east - tile_west) * (px + 1) / tileSize;
                const pixel_north = tile_north + (tile_south - tile_north) * py / tileSize;
                const pixel_south = tile_north + (tile_south - tile_north) * (py + 1) / tileSize;

                features.push({
                    type: 'Feature',
                    geometry: {
                        type: 'LineString',
                        coordinates: [
                            [pixel_west, pixel_north],
                            [pixel_east, pixel_north],
                            [pixel_east, pixel_south],
                            [pixel_west, pixel_south],
                            [pixel_west, pixel_north]
                        ]
                    },
                    properties: {
                        type: 'pixel',
                        tile_x: x_tile,
                        tile_y: y_tile,
                        pixel_x: px,
                        pixel_y: py
                    }
                });
            }
        }
        return features;
    }

    // Add click handler for selecting tiles
    setupTileSelection() {
        this.map.on('click', (e) => {
            if (this.pixelDebugEnabled) {
                const zoom = Math.floor(this.map.getZoom());
                const coords = this.getTileCoordinates(e.lngLat.lng, e.lngLat.lat, zoom);

                // Update selected tile
                this.selectedTile = {
                    x: coords.x,
                    y: coords.y,
                    z: coords.z
                };

                // Update the pixel grid
                this.updatePixelGrid();
            }
        });
    }

    togglePixelDebug() {
        if (this.pixelDebugEnabled) {
            if (this.map.getLayer('pixel-debug-grid')) {
                this.map.removeLayer('pixel-debug-grid');
            }
            if (this.map.getSource('pixel-debug-source')) {
                this.map.removeSource('pixel-debug-source');
            }
            this.selectedTile = null; // Reset selected tile
            this.pixelDebugEnabled = false;
        } else {
            this.map.addSource('pixel-debug-source', {
                'type': 'geojson',
                'data': {
                    'type': 'FeatureCollection',
                    'features': []  // Start empty until a tile is selected
                }
            });

            this.map.addLayer({
                'id': 'pixel-debug-grid',
                'type': 'line',
                'source': 'pixel-debug-source',
                'layout': {
                    'line-join': 'round',
                    'line-cap': 'round'
                },
                'paint': {
                    'line-color': '#00FF00',
                    'line-width': 0.5,
                    'line-opacity': 0.1
                }
            });

            this.pixelDebugEnabled = true;
            this.setupTileSelection(); // Setup click handling
        }
    }

    updatePixelGrid() {
        if (this.pixelDebugEnabled) {
            const bounds = this.map.getBounds();
            const zoom = Math.floor(this.map.getZoom());

            const source = this.map.getSource('pixel-debug-source');
            if (source) {
                source.setData({
                    'type': 'FeatureCollection',
                    'features': this.createPixelGrid(
                        bounds.getWest(),
                        bounds.getSouth(),
                        bounds.getEast(),
                        bounds.getNorth(),
                        zoom
                    )
                });
            }
        }
    }

    addDebugControls() {

        // Set up click handlers for existing buttons
        document.getElementById('show-tile-borders').addEventListener('click', () => {
            this.toggleTileDebug();
            document.getElementById('show-tile-borders').classList.toggle('active', this.tileDebugEnabled);
        });

        document.getElementById('show-pixel-grid').addEventListener('click', () => {
            this.togglePixelDebug();
            this.selectedTile = null;
            document.getElementById('show-pixel-grid').classList.toggle('active', this.pixelDebugEnabled);
        });

        // Update popup styling
        this.map.on('click', (e) => {
            if (this.tileDebugEnabled) {
                const zoom = Math.floor(this.map.getZoom());
                const tile = this.getTileCoordinates(e.lngLat.lng, e.lngLat.lat, zoom);

                new mapboxgl.Popup({
                    closeButton: true,
                    className: 'hint',
                })
                .setLngLat(e.lngLat)
                .setHTML(`
                    <div class="popup">
                        <h4>Tile Information</h4>
                        <p>X: ${tile.x}</p>
                        <p>Y: ${tile.y}</p>
                        <p>Zoom: ${zoom}</p>
                    </div>
                `)
                .addTo(this.map);
            }
        });
    }

    getTileCoordinates(lng, lat, zoom) {
        // Convert lng/lat to tile coordinates
        const n = Math.pow(2, zoom);
        const x = Math.floor((lng + 180) / 360 * n);
        const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n);
        return { x, y, z: zoom };
    }
}

// Function to add a location when right-clicking:
export async function addLocation(longitude, latitude) {
     try {
        const response = await fetch('/api/viewing-locations/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                name: `Location at ${latitude.toFixed(2)}, ${longitude.toFixed(2)}`,
                latitude: latitude,
                longitude: longitude,
                elevation: 0  // We could fetch actual elevation data here
            })
        });

        if (response.ok) {
            // Refresh the locations on the map
            const mapController = window.mapController;  // We'll need to make this accessible
            await mapController.loadLocationsAndEvents();

            // Close any open popups
            const popups = document.getElementsByClassName('mapboxgl-popup');
            if (popups.length) {
                popups[0].remove();
            }
        } else {
            console.error('Failed to add location');
        }
    } catch (error) {
        console.error('Error adding location:', error);
    }
}

// Function to add an event when right-clicking:
export async function addEvent(longitude, latitude) {
    // Create a form popup for event details
    const formPopupContent = `
        <div class="popup">
            <h4>Add Celestial Event</h4>
            <form id="eventForm" onsubmit="return submitEventForm(${longitude}, ${latitude})">
                <div class="form-group">
                    <input type="text" class="form-control" id="eventName" placeholder="Event Name" required>
                </div>
                <div class="form-group">
                    <select class="form-control" id="eventType" required>
                        <option value="">Select Event Type</option>
                        <option value="METEOR">Meteor Shower</option>
                        <option value="ECLIPSE">Eclipse</option>
                        <option value="PLANET">Planetary Event</option>
                        <option value="AURORA">Aurora</option>
                        <option value="COMET">Comet</option>
                        <option value="OTHER">Other</option>
                    </select>
                </div>
                <div class="form-group">
                    <input type="datetime-local" class="form-control" id="startTime" required>
                    <small class="text-muted">Start Time</small>
                </div>
                <div class="form-group">
                    <input type="datetime-local" class="form-control" id="endTime" required>
                    <small class="text-muted">End Time</small>
                </div>
                <div class="form-group">
                    <input type="number" class="form-control" id="viewingRadius"
                           placeholder="Viewing Radius (km)" required min="0">
                </div>
                <div class="form-group">
                    <textarea class="form-control" id="description"
                              placeholder="Description" required></textarea>
                </div>
                <div class="form-group">
                    <button type="submit" class="btn">Add Event</button>
                </div>
            </form>
        </div>
    `;

    // Remove any existing popups
    const popups = document.getElementsByClassName('mapboxgl-popup');
    while(popups[0]) {
        popups[0].remove();
    }

    // Show the form popup
    new mapboxgl.Popup({
        closeButton: true,
        closeOnClick: false,
    })
    .setLngLat([longitude, latitude])
    .setHTML(formPopupContent)
    .addTo(window.mapController.map);
}

// Function to submit an event form to the API:
export async function submitEventForm(longitude, latitude) {
    event.preventDefault();  // Add this line

    const formData = {
        name: document.getElementById('eventName').value,
        event_type: document.getElementById('eventType').value,
        start_time: document.getElementById('startTime').value,
        end_time: document.getElementById('endTime').value,
        viewing_radius: document.getElementById('viewingRadius').value,
        description: document.getElementById('description').value,
        longitude: longitude,
        latitude: latitude,
        elevation: 0
    };

    try {
        const response = await fetch('/api/celestial-events/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            // Refresh the events on the map
            await window.mapController.loadLocationsAndEvents();

            // Close any open popups
            const popups = document.getElementsByClassName('mapboxgl-popup');
            while(popups[0]) {
                popups[0].remove();
            }
        } else {
            console.error('Failed to add event', response);
            alert('Failed to add event. Please try again.');
        }
    } catch (error) {
        console.error('Error adding event:', error);
        alert('Error adding event. Please try again.');
    }

    return false; // Prevent form submission
}