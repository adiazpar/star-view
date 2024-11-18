function initNavbar() {

    // Create the navbar drop down menu:
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('nav-links');
    const authLinks = document.getElementById('auth-links');

    // Remove any existing click listeners:
    hamburger.replaceWith(hamburger.cloneNode(true));

    // Get the new hamburger element after replacement:
    const newHamburger = document.getElementById('hamburger');

    newHamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        authLinks.classList.toggle('active');
        console.log('ping');
    });

    // Change the nav-item color based on the current URL:
    const links = document.querySelectorAll('.nav-link');
    const currentLocation = location.href;
    links.forEach(link => {
        if (link.href === currentLocation) {
            link.classList.add('active');
        }
    });
}

// Call initNavbar when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initNavbar };
}