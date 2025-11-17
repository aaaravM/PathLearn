document.addEventListener('DOMContentLoaded', () => {
    const counters = document.querySelectorAll('[data-counter]');
    counters.forEach(counter => animateCounter(counter));
});

function animateCounter(element) {
    const target = parseInt(element.dataset.counter, 10);
    let current = 0;
    const step = Math.max(1, Math.floor(target / 120));
    const timer = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }
        element.textContent = current.toLocaleString();
    }, 20);
}
