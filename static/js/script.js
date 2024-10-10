document.addEventListener('DOMContentLoaded', function() {
    // Create the navbar drop down menu:
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('nav-links');
    const authLinks = document.getElementById('auth-links');

    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        authLinks.classList.toggle('active');
    });

    // Change the nav-item color based on the current URL:
    const links = document.querySelectorAll('.nav-link');

    window.addEventListener('load', function() {
        const currentLocation = location.href;
        links.forEach(link => {
            if (link.href === currentLocation) {
                link.classList.add('active');
            }
        });
    });
});