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



// ============================================================================
// Light Mode & Dark Mode Toggling:
// ============================================================================

// Update logo based on theme:
function updateLogo() {
    const html = document.documentElement;
    const logo = document.querySelector('.logo');
    const currentTheme = html.getAttribute('data-theme');

    // If light mode, use dark logo (dark logo on light background)
    // If dark mode, use light logo (light logo on dark background)
    if (currentTheme === 'light') {
        logo.src = '/static/images/logo-light.png';
    } else {
        logo.src = '/static/images/logo-dark.png';
    }
}

// Toggle between light and dark theme:
function toggleTheme() {
    const html = document.documentElement;
    const themeToggle = document.querySelector('.theme-toggle');
    const currentTheme = html.getAttribute('data-theme');

    // Add scale-out class to trigger animation
    themeToggle.classList.add('scale-out');

    // Wait for scale-out to complete, then switch theme
    setTimeout(() => {
        // Toggle theme
        if (currentTheme === 'light') {
            html.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            html.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }

        // Update logo after theme change
        updateLogo();

        // Remove scale-out and add scale-in class
        themeToggle.classList.remove('scale-out');
        themeToggle.classList.add('scale-in');

        // Remove scale-in class after animation completes
        setTimeout(() => {
            themeToggle.classList.remove('scale-in');
        }, 350); // Match scaleIn animation duration
    }, 200); // Wait for scaleOut animation to complete
}

// Load saved theme preference on page load:
function loadTheme() {

    updateLogo();

    const savedTheme = localStorage.getItem('theme');
    const html = document.documentElement;

    if (savedTheme) {
        html.setAttribute('data-theme', savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        html.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
}

// Listen for system theme preference changes
function setupSystemThemeListener() {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

    // Only react to system changes if user hasn't set a manual preference
    darkModeQuery.addEventListener('change', (e) => {
        const savedTheme = localStorage.getItem('theme');

        // Only apply system preference if user hasn't manually chosen a theme
        if (!savedTheme) {
            const html = document.documentElement;
            html.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            updateLogo();
        }
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initMessages();
    loadTheme();
    setupSystemThemeListener();

    // Add click handler to theme toggle button
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});
