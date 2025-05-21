// Random particle animation
document.addEventListener("DOMContentLoaded", function () {
  const particlesContainer = document.getElementById("particles");

  // Check if the particles container exists
  if (particlesContainer) {
    console.log("Particles container found, creating particles...");

    for (let i = 0; i < 100; i++) {
      // Increased from 50 to 100 particles
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
      particle.style.animationDuration = Math.random() * 4 + 2 + "s"; // Even faster movement (2-6 seconds)
      particle.style.animationDelay = Math.random() * 1.5 + "s"; // Shorter delay (0-1.5 seconds)

      particlesContainer.appendChild(particle);
    }
  } else {
    console.error("Particles container not found!");
  }
});
