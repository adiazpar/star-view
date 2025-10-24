/**
 * Location details page initialization
 *
 * Sets up the global configuration object by reading data attributes
 * from the page container. This configuration is used by the reviews
 * section and other components on the location details page.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Get the location details page container
    const pageContainer = document.querySelector('.location-details-page');
    if (!pageContainer) {
        console.error('Location details page container not found');
        return;
    }

    // Read configuration from data attributes
    const config = pageContainer.dataset;

    // Create global configuration object for backward compatibility
    // with existing reviews_section.js code
    window.locationDetailsConfig = {
        locationId: parseInt(config.locationId, 10),
        isAuthenticated: config.isAuthenticated === 'true',
        isOwner: config.isOwner === 'true',
        currentUsername: config.currentUsername || '',
        locationLongitude: parseFloat(config.locationLongitude),
        locationLatitude: parseFloat(config.locationLatitude),
        locationName: config.locationName || '',
        locationFormattedAddress: config.locationFormattedAddress || '',
        userHasReviewed: config.userHasReviewed === 'true'
    };

    console.log('✅ Location details config initialized:', window.locationDetailsConfig);
});
