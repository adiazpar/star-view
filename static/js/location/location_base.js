// Location Details - Main Orchestrator
document.addEventListener('DOMContentLoaded', function() {
    // Get configuration directly from template
    const config = window.locationDetailsConfig;
    
    // Validate configuration
    if (!config || !config.locationId) {
        console.error('Invalid configuration - some components may not work properly');
        return;
    }
    
    // Add CSRF token to config
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    config.csrfToken = csrfToken ? csrfToken.value : '';
    
    // Create simple event bus for component communication
    const eventBus = {
        events: {},
        on: function(event, callback) {
            if (!this.events[event]) this.events[event] = [];
            this.events[event].push(callback);
        },
        emit: function(event, data) {
            if (this.events[event]) {
                this.events[event].forEach(callback => callback(data));
            }
        },
        off: function(event, callback) {
            if (this.events[event]) {
                this.events[event] = this.events[event].filter(cb => cb !== callback);
            }
        }
    };
    
    // Initialize all components
    initializeComponents(config, eventBus);
    
    // Initialize non-componentized features
    initializeRemainingFeatures(config, eventBus);
});

function initializeComponents(config, eventBus) {
    // Initialize core systems in order of dependency
    if (window.EditingSystem) {
        window.EditingSystem.init(config, eventBus);
    }
    
    if (window.VotingSystem) {
        window.VotingSystem.init(config, eventBus);
    }
    
    if (window.ReviewSystem) {
        window.ReviewSystem.init(config, eventBus);
    }
    
    if (window.CommentSystem) {
        window.CommentSystem.init(config, eventBus);
    }
    
    if (window.ImageUploadSystem) {
        window.ImageUploadSystem.init();
    }
    
    if (window.ReportModal) {
        window.ReportModal.init(config, eventBus);
    }
    
    console.log('Location details components initialized');
}

function initializeRemainingFeatures(config, eventBus) {
    // Initialize favorite functionality
    if (config.isAuthenticated) {
        initializeFavoriteSystem(config);
    }
}







// Favorite functionality
function initializeFavoriteSystem(config) {
    let isFavorited = false;
    let favoriteId = null;

    function updateFavoriteButton() {
        const favoriteButton = document.querySelector('.favorite-button');
        const favoriteText = document.getElementById('favoriteText');

        if (favoriteButton && favoriteText) {
            favoriteButton.classList.toggle('favorited', isFavorited);
            favoriteText.textContent = isFavorited ? 'Remove from Favorites' : 'Add to Favorites';
        }
    }

    // Check initial favorite status by fetching location data
    const favoriteButton = document.querySelector('.favorite-button');
    if (favoriteButton) {
        fetch(`/api/locations/${config.locationId}/`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            isFavorited = data.is_favorited;
            updateFavoriteButton();

            // If favorited, get the favorite ID for potential unfavorite operation
            if (isFavorited) {
                return fetch('/api/favorite-locations/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'same-origin'
                });
            }
        })
        .then(response => {
            if (response) return response.json();
        })
        .then(favorites => {
            if (favorites && favorites.results) {
                const favorite = favorites.results.find(f => f.location.id === config.locationId);
                if (favorite) favoriteId = favorite.id;
            }
        })
        .catch(error => console.error('Error checking favorite status:', error));

        // Add click handler for favorite button
        favoriteButton.addEventListener('click', async function() {
            try {
                if (isFavorited) {
                    // Unfavorite: DELETE the favorite
                    if (!favoriteId) {
                        // Fetch favorite ID if we don't have it
                        const favoritesResponse = await fetch('/api/favorite-locations/', {
                            method: 'GET',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            credentials: 'same-origin'
                        });
                        const favorites = await favoritesResponse.json();
                        const favorite = favorites.results ? favorites.results.find(f => f.location.id === config.locationId) : null;
                        if (favorite) favoriteId = favorite.id;
                    }

                    if (favoriteId) {
                        const response = await fetch(`/api/favorite-locations/${favoriteId}/`, {
                            method: 'DELETE',
                            headers: {
                                'X-CSRFToken': config.csrfToken,
                                'Content-Type': 'application/json'
                            },
                            credentials: 'same-origin'
                        });

                        if (!response.ok) throw new Error('Failed to unfavorite');

                        isFavorited = false;
                        favoriteId = null;
                        updateFavoriteButton();
                    }
                } else {
                    // Favorite: POST to create new favorite
                    const response = await fetch('/api/favorite-locations/', {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': config.csrfToken,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            location_id: config.locationId
                        }),
                        credentials: 'same-origin'
                    });

                    if (!response.ok) throw new Error('Failed to favorite');

                    const data = await response.json();
                    favoriteId = data.id;
                    isFavorited = true;
                    updateFavoriteButton();
                }
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            }
        });
    }
}

