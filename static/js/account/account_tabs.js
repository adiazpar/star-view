/**
 * Account page tab management
 *
 * Handles the active state of sidebar tabs based on URL parameters.
 * Ensures the correct tab is highlighted when navigating between
 * Profile and Favorites sections.
 */

export function initAccountTabs() {
    document.addEventListener('DOMContentLoaded', () => {
        // Get the current tab from URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const currentTab = urlParams.get('tab') || 'profile';  // Default to profile if no tab

        // Add active class to the current tab
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        sidebarItems.forEach(item => {
            const link = item.querySelector('.sidebar-link');
            if (!link) return;

            const linkTab = new URLSearchParams(link.href.split('?')[1])?.get('tab');

            if (linkTab === currentTab) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    });
}
