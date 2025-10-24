/**
 * Base template initialization
 *
 * Initializes functionality that should be available on every page:
 * - Navbar: Hamburger menu, active link highlighting
 * - Messages: Display and dismissal of Django messages
 */

import { initMessages } from './utils/util_messages.js';

/**
 * Initialize navbar functionality
 * - Hamburger menu toggle for mobile
 * - Active link highlighting based on current URL
 */
function initNavbar() {
    // Create the navbar drop down menu:
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('nav-links');
    const authLinks = document.getElementById('auth-links');

    if (!hamburger || !navLinks || !authLinks) return;

    // Remove any existing click listeners:
    hamburger.replaceWith(hamburger.cloneNode(true));

    // Get the new hamburger element after replacement:
    const newHamburger = document.getElementById('hamburger');

    newHamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        authLinks.classList.toggle('active');
    });

    // Change the nav-item color based on the current URL:
    const links = document.querySelectorAll('.nav-link');
    const currentLocation = location.href;

    links.forEach(link => {
        // Skip links with href="#"
        if (link.getAttribute('href') === '#') {
            return;
        }

        // Get the base URL without query parameters for both current location and link:
        const currentBasePath = currentLocation.split('?')[0];
        const linkBasePath = link.href.split('?')[0];

        // Check if the base paths match:
        if (currentBasePath === linkBasePath ||
            (link.href.includes('/account/') && currentLocation.includes('/account/'))) {
            link.classList.add('active');
        }
        else {
            link.classList.remove('active');
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    initMessages();
});

// Re-initialize navbar when URL changes without page reload:
window.addEventListener('popstate', () => {
    initNavbar();
});
