// Create and animate stars in the background
document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('starsContainer');

    function createStar() {
        const star = document.createElement('div');
        star.className = 'star';

        // Random position with padding from edges
        star.style.left = `${5 + Math.random() * 90}%`;
        star.style.top = `${5 + Math.random() * 90}%`;

        // Smaller size range for more subtle effect
        const size = Math.random() * 2 + 0.5; // Between 0.5px and 2.5px
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;

        // Varied animation speeds for more natural effect
        const speed = Math.random() * 3 + 2; // Between 2 and 5 seconds
        star.style.animationDuration = `${speed}s`;

        // Random initial delay to prevent all stars starting at once
        star.style.animationDelay = `${Math.random() * 5}s`;

        // Set initial opacity based on size for depth effect
        const initialOpacity = 0.3 + (size / 2.5) * 0.3; // Larger stars slightly brighter
        star.style.opacity = initialOpacity;

        return star;
    }

    // Create stars in batches for better performance
    function createStarField(count) {
        const fragment = document.createDocumentFragment();
        for (let i = 0; i < count; i++) {
            fragment.appendChild(createStar());
        }
        container.appendChild(fragment);
    }

    // Create initial set of stars
    createStarField(100); // Reduced number for subtlety

    // Occasionally add new stars for subtle variation
    setInterval(() => {
        const oldStar = container.firstChild;
        if (oldStar) {
            oldStar.remove();
        }
        container.appendChild(createStar());
    }, 3000);
});