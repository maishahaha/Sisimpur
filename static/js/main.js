// main.js
// Place this in static/js/main.js

const countdownDate = new Date();
countdownDate.setDate(countdownDate.getDate() + 30);

function updateCountdown() {
    const now = new Date().getTime();
    const distance = countdownDate - now;
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    document.getElementById("days").innerText = days;
    document.getElementById("hours").innerText = hours;
    document.getElementById("minutes").innerText = minutes;
    document.getElementById("seconds").innerText = seconds;

    if (distance < 0) {
        clearInterval(x);
        document.getElementById("days").innerText = "0";
        document.getElementById("hours").innerText = "0";
        document.getElementById("minutes").innerText = "0";
        document.getElementById("seconds").innerText = "0";
    }
}

updateCountdown();
const x = setInterval(updateCountdown, 1000);

const particlesContainer = document.getElementById('particles');
const particleCount = 50;
for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.classList.add('particle');
    const posX = Math.random() * 100;
    const posY = Math.random() * 100;
    particle.style.left = posX + '%';
    particle.style.top = posY + '%';
    const size = Math.random() * 3 + 1;
    particle.style.width = size + 'px';
    particle.style.height = size + 'px';
    const duration = Math.random() * 50 + 20;
    const delay = Math.random() * 10;
    particle.style.animation = `fadeInOut ${duration}s infinite ${delay}s`;
    particlesContainer.appendChild(particle);
}

// Handle subscription form submissions
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.subscribe-form').forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const email = this.querySelector('input[name="email"]').value;
            const responseDiv = this.closest('div').querySelector('.form-response');

            if (!email) {
                responseDiv.innerHTML = '<div class="alert alert-danger">Please enter a valid email address.</div>';
                return;
            }

            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            // Show loading state
            responseDiv.innerHTML = '<div class="text-white">Subscribing...</div>';

            // Send AJAX request to the backend
            fetch('/api/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ email: email })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    responseDiv.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    form.reset();
                } else {
                    // Check if it's an already subscribed error
                    if (data.error && data.error.includes('already subscribed')) {
                        responseDiv.innerHTML = '<div class="alert alert-info">This email is already in our list. Thank you!</div>';
                    } else {
                        responseDiv.innerHTML = '<div class="alert alert-danger">' + (data.error || 'An error occurred. Please try again.') + '</div>';
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                responseDiv.innerHTML = '<div class="alert alert-danger">An error occurred. Please try again later.</div>';
            });
        });
    });
});