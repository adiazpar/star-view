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

    function updateFavoriteButton() {
        const favoriteButton = document.querySelector('.favorite-button');
        const favoriteText = document.getElementById('favoriteText');

        if (favoriteButton && favoriteText) {
            favoriteButton.classList.toggle('favorited', isFavorited);
            favoriteText.textContent = isFavorited ? 'Remove from Favorites' : 'Add to Favorites';
        }
    }

    // Check initial favorite status when page loads
    const favoriteButton = document.querySelector('.favorite-button');
    if (favoriteButton) {
        fetch(`/api/viewing-locations/${config.locationId}/favorite/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': config.csrfToken,
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            isFavorited = data.is_favorited;
            updateFavoriteButton();
        })
        .catch(error => console.error('Error checking favorite status:', error));

        // Add click handler for favorite button
        favoriteButton.addEventListener('click', function() {
            const endpoint = isFavorited ? 'unfavorite' : 'favorite';

            fetch(`/api/viewing-locations/${config.locationId}/${endpoint}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': config.csrfToken,
                    'Content-Type': 'application/json'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                isFavorited = !isFavorited;
                updateFavoriteButton();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        });
    }
}

