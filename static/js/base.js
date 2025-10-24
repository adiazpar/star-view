/**
 * Base template initialization
 *
 * Initializes functionality that should be available on every page:
 * - Mobile hamburger menu toggle
 * - Message system initialization
 */

import { initMessages } from './utils/util_messages.js';

// ============================================================================
// CSS CLASSES - Update these if you rename CSS classes
// ============================================================================
const CSS_CLASSES = {
    NAV_MENU: 'nav-menu',
    NAV_BACKDROP: 'nav-backdrop',
    HAMBURGER: 'hamburger',
    MENU_ICON: 'menu-icon',
    X_ICON: 'x-icon',
    ACTIVE: 'active'
};

/**
 * Toggle mobile navigation menu
 */
window.toggleMenu = function() {
    const navMenu = document.querySelector(`.${CSS_CLASSES.NAV_MENU}`);
    const navBackdrop = document.querySelector(`.${CSS_CLASSES.NAV_BACKDROP}`);
    const menuIcon = document.querySelector(`.${CSS_CLASSES.MENU_ICON}`);
    const xIcon = document.querySelector(`.${CSS_CLASSES.X_ICON}`);

    // Toggle menu and backdrop
    navMenu.classList.toggle(CSS_CLASSES.ACTIVE);
    navBackdrop.classList.toggle(CSS_CLASSES.ACTIVE);

    // Switch between hamburger and X icons
    if (navMenu.classList.contains(CSS_CLASSES.ACTIVE)) {
        menuIcon.style.display = 'none';
        xIcon.style.display = 'block';
    } else {
        menuIcon.style.display = 'block';
        xIcon.style.display = 'none';
    }
}

/**
 * Close mobile navigation menu
 */
function closeMenu() {
    const navMenu = document.querySelector(`.${CSS_CLASSES.NAV_MENU}`);
    const navBackdrop = document.querySelector(`.${CSS_CLASSES.NAV_BACKDROP}`);
    const menuIcon = document.querySelector(`.${CSS_CLASSES.MENU_ICON}`);
    const xIcon = document.querySelector(`.${CSS_CLASSES.X_ICON}`);

    navMenu.classList.remove(CSS_CLASSES.ACTIVE);
    navBackdrop.classList.remove(CSS_CLASSES.ACTIVE);
    menuIcon.style.display = 'block';
    xIcon.style.display = 'none';
}

/**
 * Close menu when clicking outside the menu area
 */
document.addEventListener('click', function(e) {
    const hamburger = document.querySelector(`.${CSS_CLASSES.HAMBURGER}`);
    const navMenu = document.querySelector(`.${CSS_CLASSES.NAV_MENU}`);

    if (navMenu.classList.contains(CSS_CLASSES.ACTIVE) &&
        !navMenu.contains(e.target) &&
        !hamburger.contains(e.target)) {
        closeMenu();
    }
});

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initMessages();
});
