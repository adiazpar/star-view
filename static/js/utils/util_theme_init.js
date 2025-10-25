/**
 * Theme initialization utility
 *
 * This script runs synchronously in the <head> before CSS loads to prevent
 * the flash of unstyled content (FOUC) when the page loads with a cached theme.
 *
 * IMPORTANT: This file must be loaded as a regular script (not a module) and
 * must run before CSS is applied.
 */

(function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    } else {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', prefersDark ? 'dark' : 'light');
    }
})();
