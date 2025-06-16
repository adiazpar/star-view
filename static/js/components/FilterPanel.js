/**
 * FilterPanel Component
 * Handles advanced filtering functionality for the map interface
 */
export class FilterPanel {
    constructor(options = {}) {
        this.container = options.container || document.querySelector('.filter-panel');
        this.onFilterChange = options.onFilterChange || (() => {});
        this.csrfToken = options.csrfToken || document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        this.filters = {
            // Location filters
            is_verified: false,
            min_quality_score: 0,
            max_quality_score: 100,
            min_light_pollution: 0,
            max_light_pollution: 30,
            min_rating: 0,
            radius: null,
            lat: null,
            lng: null,
            categories: [],
            tags: [],
            
            // Event filters (existing)
            eventTypes: []
        };
        
        this.init();
    }

    init() {
        if (!this.container) return;
        
        this.loadCategories();
        this.loadTags();
        this.enhanceExistingFilters();
        this.addAdvancedFilters();
        this.attachEventListeners();
    }

    async loadCategories() {
        try {
            const response = await fetch('/api/v1/location-categories/', {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.categories = data.results || data;
                this.renderCategoryFilters();
            } else {
                console.warn('Categories endpoint not available:', response.status);
            }
        } catch (error) {
            console.warn('Error loading categories:', error);
            // Gracefully handle missing categories - just hide the category section
            const categorySection = this.advancedSection?.querySelector('#categoryFilters');
            if (categorySection) {
                categorySection.style.display = 'none';
            }
        }
    }

    async loadTags() {
        try {
            const response = await fetch('/api/v1/location-tags/', {
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.tags = data.results || data;
                this.renderTagFilters();
            } else {
                console.warn('Tags endpoint not available:', response.status);
            }
        } catch (error) {
            console.warn('Error loading tags:', error);
            // Gracefully handle missing tags - just hide the tag section
            const tagSection = this.advancedSection?.querySelector('#tagFilters');
            if (tagSection) {
                tagSection.style.display = 'none';
            }
        }
    }

    enhanceExistingFilters() {
        // Add to existing location-type-filter section
        const locationFilterSection = this.container.querySelector('.location-type-filter');
        if (locationFilterSection) {
            const advancedToggle = document.createElement('button');
            advancedToggle.className = 'advanced-filters-toggle';
            advancedToggle.innerHTML = '<i class="fas fa-sliders-h"></i> Advanced Filters';
            locationFilterSection.appendChild(advancedToggle);
        }
    }

    addAdvancedFilters() {
        const advancedSection = document.createElement('div');
        advancedSection.className = 'advanced-filters-section';
        advancedSection.style.display = 'none';
        advancedSection.innerHTML = `
            <div class="filter-group">
                <h4>Location Quality</h4>
                
                <div class="filter-item">
                    <label class="checkbox-label">
                        <input type="checkbox" id="verifiedOnly" class="filter-checkbox">
                        <span>Verified Locations Only</span>
                    </label>
                </div>
                
                <div class="filter-item">
                    <label>Quality Score</label>
                    <div class="range-slider-container">
                        <input type="range" id="qualityMin" min="0" max="100" value="0" class="range-slider">
                        <input type="range" id="qualityMax" min="0" max="100" value="100" class="range-slider">
                        <div class="range-values">
                            <span id="qualityMinValue">0</span> - <span id="qualityMaxValue">100</span>
                        </div>
                    </div>
                </div>
                
                <div class="filter-item">
                    <label>Light Pollution (mag/arcsec²)</label>
                    <div class="range-slider-container">
                        <input type="range" id="pollutionMin" min="0" max="30" step="0.1" value="0" class="range-slider">
                        <input type="range" id="pollutionMax" min="0" max="30" step="0.1" value="30" class="range-slider">
                        <div class="range-values">
                            <span id="pollutionMinValue">0</span> - <span id="pollutionMaxValue">30</span>
                        </div>
                    </div>
                </div>
                
                <div class="filter-item">
                    <label>Minimum Rating</label>
                    <div class="star-filter">
                        <input type="range" id="minRating" min="0" max="5" step="0.5" value="0" class="star-slider">
                        <div class="star-display">
                            <span id="ratingValue">Any</span>
                            <div class="stars" id="ratingStars"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="filter-group">
                <h4>Location Search</h4>
                
                <div class="filter-item">
                    <label>Search Radius (km)</label>
                    <div class="radius-search">
                        <input type="number" id="searchRadius" min="1" max="500" placeholder="e.g., 50" class="radius-input">
                        <button class="btn-location" id="useMyLocation">
                            <i class="fas fa-crosshairs"></i> Use My Location
                        </button>
                    </div>
                    <div class="location-display" id="locationDisplay" style="display: none;">
                        <i class="fas fa-map-marker-alt"></i>
                        <span id="locationText"></span>
                        <button class="btn-clear" id="clearLocation">&times;</button>
                    </div>
                </div>
            </div>
            
            <div class="filter-group" id="categoryFilters">
                <h4>Categories</h4>
                <div class="category-grid"></div>
            </div>
            
            <div class="filter-group" id="tagFilters">
                <h4>Popular Tags</h4>
                <div class="tag-cloud"></div>
            </div>
            
            <div class="filter-actions">
                <button class="btn-clear-filters" id="clearAllFilters">
                    <i class="fas fa-times"></i> Clear All
                </button>
                <button class="btn-apply-filters" id="applyFilters">
                    <i class="fas fa-check"></i> Apply Filters
                </button>
            </div>
        `;
        
        this.container.appendChild(advancedSection);
        this.advancedSection = advancedSection;
    }

    renderCategoryFilters() {
        const categoryGrid = this.advancedSection?.querySelector('.category-grid');
        if (!categoryGrid || !this.categories) return;
        
        categoryGrid.innerHTML = this.categories.map(cat => `
            <label class="category-filter-item">
                <input type="checkbox" value="${cat.slug}" class="category-checkbox">
                <span class="category-label">
                    <i class="${cat.icon}"></i>
                    ${cat.name}
                </span>
            </label>
        `).join('');
    }

    renderTagFilters() {
        const tagCloud = this.advancedSection?.querySelector('.tag-cloud');
        if (!tagCloud || !this.tags) return;
        
        // Show only top 20 most used tags
        const topTags = this.tags
            .sort((a, b) => b.usage_count - a.usage_count)
            .slice(0, 20);
        
        tagCloud.innerHTML = topTags.map(tag => `
            <button class="tag-filter-chip" data-tag="${tag.slug}">
                #${tag.name} (${tag.usage_count})
            </button>
        `).join('');
    }

    attachEventListeners() {
        // Toggle advanced filters
        const advancedToggle = this.container.querySelector('.advanced-filters-toggle');
        if (advancedToggle) {
            advancedToggle.addEventListener('click', () => {
                const isVisible = this.advancedSection.style.display !== 'none';
                this.advancedSection.style.display = isVisible ? 'none' : 'block';
                advancedToggle.classList.toggle('active', !isVisible);
            });
        }

        // Verified only checkbox
        const verifiedCheckbox = document.getElementById('verifiedOnly');
        if (verifiedCheckbox) {
            verifiedCheckbox.addEventListener('change', (e) => {
                this.filters.is_verified = e.target.checked;
            });
        }

        // Quality score sliders
        this.setupRangeSlider('quality', 'min_quality_score', 'max_quality_score', 0, 100);
        
        // Light pollution sliders
        this.setupRangeSlider('pollution', 'min_light_pollution', 'max_light_pollution', 0, 30, 0.1);
        
        // Rating slider
        const ratingSlider = document.getElementById('minRating');
        if (ratingSlider) {
            ratingSlider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                this.filters.min_rating = value;
                this.updateRatingDisplay(value);
            });
            this.updateRatingDisplay(0);
        }

        // Location search
        const useLocationBtn = document.getElementById('useMyLocation');
        if (useLocationBtn) {
            useLocationBtn.addEventListener('click', () => this.useCurrentLocation());
        }

        const clearLocationBtn = document.getElementById('clearLocation');
        if (clearLocationBtn) {
            clearLocationBtn.addEventListener('click', () => this.clearLocation());
        }

        const radiusInput = document.getElementById('searchRadius');
        if (radiusInput) {
            radiusInput.addEventListener('change', (e) => {
                this.filters.radius = e.target.value ? parseInt(e.target.value) : null;
            });
        }

        // Category checkboxes
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('category-checkbox')) {
                this.updateCategoryFilters();
            }
        });

        // Tag chips
        this.container.addEventListener('click', (e) => {
            if (e.target.classList.contains('tag-filter-chip')) {
                e.target.classList.toggle('active');
                this.updateTagFilters();
            }
        });

        // Apply and clear buttons
        const applyBtn = document.getElementById('applyFilters');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyFilters());
        }

        const clearBtn = document.getElementById('clearAllFilters');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAllFilters());
        }
    }

    setupRangeSlider(name, minProp, maxProp, min, max, step = 1) {
        const minSlider = document.getElementById(`${name}Min`);
        const maxSlider = document.getElementById(`${name}Max`);
        const minValue = document.getElementById(`${name}MinValue`);
        const maxValue = document.getElementById(`${name}MaxValue`);

        if (!minSlider || !maxSlider) return;

        const updateSliders = () => {
            const minVal = parseFloat(minSlider.value);
            const maxVal = parseFloat(maxSlider.value);

            if (minVal > maxVal) {
                if (event.target === minSlider) {
                    maxSlider.value = minVal;
                } else {
                    minSlider.value = maxVal;
                }
            }

            this.filters[minProp] = parseFloat(minSlider.value);
            this.filters[maxProp] = parseFloat(maxSlider.value);

            if (minValue) minValue.textContent = minSlider.value;
            if (maxValue) maxValue.textContent = maxSlider.value;
        };

        minSlider.addEventListener('input', updateSliders);
        maxSlider.addEventListener('input', updateSliders);
    }

    updateRatingDisplay(value) {
        const ratingValue = document.getElementById('ratingValue');
        const ratingStars = document.getElementById('ratingStars');
        
        if (ratingValue) {
            ratingValue.textContent = value === 0 ? 'Any' : `${value}+`;
        }
        
        if (ratingStars) {
            const fullStars = Math.floor(value);
            const hasHalfStar = value % 1 !== 0;
            
            let starsHTML = '';
            for (let i = 0; i < 5; i++) {
                if (i < fullStars) {
                    starsHTML += '<i class="fas fa-star"></i>';
                } else if (i === fullStars && hasHalfStar) {
                    starsHTML += '<i class="fas fa-star-half-alt"></i>';
                } else {
                    starsHTML += '<i class="far fa-star"></i>';
                }
            }
            ratingStars.innerHTML = starsHTML;
        }
    }

    async useCurrentLocation() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser');
            return;
        }

        const btn = document.getElementById('useMyLocation');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting location...';
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                this.filters.lat = position.coords.latitude;
                this.filters.lng = position.coords.longitude;
                this.showLocationDisplay(position.coords.latitude, position.coords.longitude);
                
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-crosshairs"></i> Use My Location';
                }
            },
            (error) => {
                console.error('Error getting location:', error);
                alert('Unable to get your location. Please check your browser settings.');
                
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<i class="fas fa-crosshairs"></i> Use My Location';
                }
            }
        );
    }

    showLocationDisplay(lat, lng) {
        const display = document.getElementById('locationDisplay');
        const text = document.getElementById('locationText');
        
        if (display && text) {
            text.textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
            display.style.display = 'flex';
        }
    }

    clearLocation() {
        this.filters.lat = null;
        this.filters.lng = null;
        this.filters.radius = null;
        
        const display = document.getElementById('locationDisplay');
        const radiusInput = document.getElementById('searchRadius');
        
        if (display) display.style.display = 'none';
        if (radiusInput) radiusInput.value = '';
    }

    updateCategoryFilters() {
        const checkboxes = this.container.querySelectorAll('.category-checkbox:checked');
        this.filters.categories = Array.from(checkboxes).map(cb => cb.value);
    }

    updateTagFilters() {
        const activeTags = this.container.querySelectorAll('.tag-filter-chip.active');
        this.filters.tags = Array.from(activeTags).map(tag => tag.dataset.tag);
    }

    applyFilters() {
        // Build filter object for API
        const activeFilters = {};
        
        // Add active filters
        if (this.filters.is_verified) activeFilters.is_verified = true;
        if (this.filters.min_quality_score > 0) activeFilters.min_quality_score = this.filters.min_quality_score;
        if (this.filters.max_quality_score < 100) activeFilters.max_quality_score = this.filters.max_quality_score;
        if (this.filters.min_light_pollution > 0) activeFilters.min_light_pollution = this.filters.min_light_pollution;
        if (this.filters.max_light_pollution < 30) activeFilters.max_light_pollution = this.filters.max_light_pollution;
        if (this.filters.min_rating > 0) activeFilters.min_rating = this.filters.min_rating;
        
        if (this.filters.radius && this.filters.lat && this.filters.lng) {
            activeFilters.radius = this.filters.radius;
            activeFilters.lat = this.filters.lat;
            activeFilters.lng = this.filters.lng;
        }
        
        if (this.filters.categories.length > 0) {
            activeFilters.categories = this.filters.categories.join(',');
        }
        
        if (this.filters.tags.length > 0) {
            activeFilters.tags = this.filters.tags.join(',');
        }
        
        // Trigger callback
        this.onFilterChange(activeFilters);
        
        // Show active filter count
        this.updateFilterCount();
    }

    clearAllFilters() {
        // Reset all filter values
        this.filters = {
            is_verified: false,
            min_quality_score: 0,
            max_quality_score: 100,
            min_light_pollution: 0,
            max_light_pollution: 30,
            min_rating: 0,
            radius: null,
            lat: null,
            lng: null,
            categories: [],
            tags: [],
            eventTypes: []
        };
        
        // Reset UI elements
        const verifiedCheckbox = document.getElementById('verifiedOnly');
        if (verifiedCheckbox) verifiedCheckbox.checked = false;
        
        // Reset sliders
        document.getElementById('qualityMin').value = 0;
        document.getElementById('qualityMax').value = 100;
        document.getElementById('pollutionMin').value = 0;
        document.getElementById('pollutionMax').value = 30;
        document.getElementById('minRating').value = 0;
        
        // Update displays
        document.getElementById('qualityMinValue').textContent = '0';
        document.getElementById('qualityMaxValue').textContent = '100';
        document.getElementById('pollutionMinValue').textContent = '0';
        document.getElementById('pollutionMaxValue').textContent = '30';
        this.updateRatingDisplay(0);
        
        // Clear location
        this.clearLocation();
        
        // Uncheck categories
        this.container.querySelectorAll('.category-checkbox').forEach(cb => cb.checked = false);
        
        // Deactivate tags
        this.container.querySelectorAll('.tag-filter-chip').forEach(tag => tag.classList.remove('active'));
        
        // Apply empty filters
        this.onFilterChange({});
        this.updateFilterCount();
        
        // Reset to original data if map controller supports it
        if (window.mapController && window.mapController.resetAdvancedFilters) {
            window.mapController.resetAdvancedFilters();
        }
    }

    updateFilterCount() {
        const filterToggle = document.getElementById('filter-toggle');
        if (!filterToggle) return;
        
        let count = 0;
        if (this.filters.is_verified) count++;
        if (this.filters.min_quality_score > 0) count++;
        if (this.filters.max_quality_score < 100) count++;
        if (this.filters.min_light_pollution > 0) count++;
        if (this.filters.max_light_pollution < 30) count++;
        if (this.filters.min_rating > 0) count++;
        if (this.filters.radius) count++;
        if (this.filters.categories.length > 0) count++;
        if (this.filters.tags.length > 0) count++;
        
        if (count > 0) {
            filterToggle.innerHTML = `<i class="fas fa-filter"></i> <span class="filter-count">${count}</span>`;
        } else {
            filterToggle.innerHTML = '<i class="fas fa-filter"></i>';
        }
    }
}