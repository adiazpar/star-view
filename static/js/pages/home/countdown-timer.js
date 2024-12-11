document.addEventListener('DOMContentLoaded', function() {
    const countdownElement = document.querySelector('.countdown-timer');
    if (!countdownElement) return;

    const targetDate = new Date(countdownElement.dataset.targetDate);

    function updateCountdown() {
        const now = new Date();
        const difference = targetDate - now;

        const days = Math.floor(difference / (1000 * 60 * 60 * 24));
        const hours = Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60));

        countdownElement.innerHTML = `
            <div>
                <div class="text-3xl font-bold">${days}</div>
                <div class="text-sm">Days</div>
            </div>
            <div>
                <div class="text-3xl font-bold">${hours}</div>
                <div class="text-sm">Hours</div>
            </div>
            <div>
                <div class="text-3xl font-bold">${minutes}</div>
                <div class="text-sm">Minutes</div>
            </div>
        `;
    }

    updateCountdown();
    setInterval(updateCountdown, 60000);
});