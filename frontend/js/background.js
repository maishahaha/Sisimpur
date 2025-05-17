// Random particle animation
const particlesContainer = document.getElementById("particles");
for (let i = 0; i < 50; i++) {
  const particle = document.createElement("div");
  particle.className = "particle";

  // Random starting position
  particle.style.left = Math.random() * 100 + "%";
  particle.style.top = Math.random() * 100 + "%";

  // Random movement direction
  const tx = (Math.random() - 0.5) * 200; // Random X movement (-100px to 100px)
  const ty = (Math.random() - 0.5) * 200; // Random Y movement (-100px to 100px)
  particle.style.setProperty("--tx", `${tx}px`);
  particle.style.setProperty("--ty", `${ty}px`);

  // Random duration and delay
  particle.style.animationDuration = Math.random() * 5 + 3 + "s"; // Faster movement (3-8 seconds)
  particle.style.animationDelay = Math.random() * 2 + "s"; // Shorter delay (0-2 seconds)

  particlesContainer.appendChild(particle);
}