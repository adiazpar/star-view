/**
 * Account Favorites Page JavaScript
 *
 * Handles all interactive functionality for the favorites page including:
 * - Search/filter favorites
 * - Nickname editing
 * - Unfavoriting locations
 * - CSRF token management
 */

/**
 * Get CSRF token from cookies
 * @param {string} name - The cookie name
 * @returns {string|null} The cookie value or null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Filter favorites based on search term
 * @param {string} searchTerm - The search term to filter by
 */
function filterFavorites(searchTerm) {
    const cards = document.querySelectorAll('.favorite-card');
    const noResults = document.querySelector('.no-results');

    if (!cards.length) return;

    searchTerm = searchTerm.toLowerCase().trim();
    let hasVisibleCards = false;

    cards.forEach(card => {
        if (!card) return;  // Skip if card is null

        const searchText = card.getAttribute('data-search-text');
        if (!searchText) return;  // Skip if no search text

        if (searchText.includes(searchTerm)) {
            card.style.display = '';  // Use default display value
            hasVisibleCards = true;
        } else {
            card.style.display = 'none';
        }
    });

    // Show/hide no results message
    if (noResults) {
        noResults.style.display = hasVisibleCards ? 'none' : 'block';
    }
}

/**
 * Toggle nickname edit mode for a favorite
 * @param {number} favoriteId - The ID of the favorite to edit
 */
export function toggleNicknameEdit(favoriteId) {
    const editContainer = document.getElementById(`nickname-edit-${favoriteId}`);

    if (editContainer.style.display === 'none') {
        editContainer.style.display = 'flex';
        editContainer.querySelector('input').focus();
    } else {
        editContainer.style.display = 'none';
    }
}

/**
 * Save nickname for a favorite location
 * @param {number} favoriteId - The ID of the favorite to update
 */
export async function saveNickname(favoriteId) {
    const input = document.querySelector(`#nickname-edit-${favoriteId} input`);
    const nickname = input.value.trim();
    const csrftoken = getCookie('csrftoken');

    // Get original name from data attribute
    const cardHeader = document.querySelector(`#nickname-edit-${favoriteId}`).closest('.favorite-header');
    const displayElement = cardHeader.querySelector('.display-name');
    const originalName = displayElement.getAttribute('data-original-name');

    try {
        const response = await fetch(`/api/favorite-locations/${favoriteId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'Accept': 'application/json, text/plain, */*'
            },
            body: JSON.stringify({ nickname: nickname || null })
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'An error occurred');
        }

        const data = await response.json();

        // Update display name
        displayElement.textContent = data.nickname || originalName;

        // Handle original name display
        let originalNameElement = cardHeader.querySelector('.original-name');
        if (!originalNameElement && nickname) {
            originalNameElement = document.createElement('div');
            originalNameElement.className = 'original-name';
            originalNameElement.title = originalName;
            cardHeader.insertBefore(originalNameElement, cardHeader.querySelector('.nickname-edit-container'));
        }

        if (originalNameElement) {
            if (nickname) {
                originalNameElement.textContent = `Originally: ${originalName}`;
                originalNameElement.style.display = 'block';
            } else {
                originalNameElement.style.display = 'none';
            }
        }

        toggleNicknameEdit(favoriteId);
    } catch (error) {
        console.error('Error:', error);
        alert(error.message);
    }
}

/**
 * Remove a location from favorites
 * @param {number} locationId - The location ID to unfavorite
 */
export async function unfavoriteLocation(locationId) {
    if (!confirm('Are you sure you want to remove this location from your favorites?')) return;

    try {
        // First, get the user's favorites to find the favorite ID
        const favoritesResponse = await fetch('/api/favorite-locations/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!favoritesResponse.ok) {
            throw new Error('Failed to fetch favorites');
        }

        const favoritesData = await favoritesResponse.json();
        const favorites = favoritesData.results || favoritesData;
        const favorite = favorites.find(f => f.location.id === locationId);

        if (!favorite) {
            throw new Error('Favorite not found');
        }

        // Delete the favorite
        const response = await fetch(`/api/favorite-locations/${favorite.id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            window.location.reload();
        } else {
            throw new Error('Failed to remove favorite');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to remove favorite. Please try again.');
    }
}

/**
 * Initialize the favorites page
 */
export function initFavoritesPage() {
    // Set up search functionality
    const searchInput = document.getElementById('favorites-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterFavorites(this.value);
        });
    }
}

// Make functions available globally for inline onclick handlers
window.toggleNicknameEdit = toggleNicknameEdit;
window.saveNickname = saveNickname;
window.unfavoriteLocation = unfavoriteLocation;
