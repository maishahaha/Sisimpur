// main.js
// Place this in static/js/main.js

const countdownDate = new Date();
countdownDate.setDate(countdownDate.getDate() + 30);

function updateCountdown() {
  const now = new Date().getTime();
  const distance = countdownDate - now;
  const days = Math.floor(distance / (1000 * 60 * 60 * 24));
  const hours = Math.floor(
    (distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
  );
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

const particlesContainer = document.getElementById("particles");
const particleCount = 50;
for (let i = 0; i < particleCount; i++) {
  const particle = document.createElement("div");
  particle.classList.add("particle");
  const posX = Math.random() * 100;
  const posY = Math.random() * 100;
  particle.style.left = posX + "%";
  particle.style.top = posY + "%";
  const size = Math.random() * 3 + 1;
  particle.style.width = size + "px";
  particle.style.height = size + "px";
  const duration = Math.random() * 50 + 20;
  const delay = Math.random() * 10;
  particle.style.animation = `fadeInOut ${duration}s infinite ${delay}s`;
  particlesContainer.appendChild(particle);
}
