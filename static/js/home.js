const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Medical Student",
    content:
      "SISIMPUR has revolutionized how I prepare for exams. The AI-generated questions are incredibly relevant and challenging.",
  },
  {
    name: "Michael Chen",
    role: "Engineering Student",
    content:
      "The platform is intuitive and the questions are well-structured. It's like having a personal tutor available 24/7.",
  },
  {
    name: "Emma Rodriguez",
    role: "Law Student",
    content:
      "I've seen a significant improvement in my test scores since using SISIMPUR. The practice questions are spot on!",
  },
  {
    name: "David Kim",
    role: "Computer Science Student",
    content:
      "The AI-generated questions are incredibly smart and adapt to my learning style. It's like having a personalized study plan.",
  },
  {
    name: "Lisa Patel",
    role: "Business Student",
    content:
      "SISIMPUR has made exam preparation so much more efficient. I can practice anywhere, anytime, and track my progress.",
  },
  {
    name: "James Wilson",
    role: "Physics Student",
    content:
      "The variety of question formats keeps me engaged and helps me understand concepts from different angles.",
  },
];

/**
 * Determines how many testimonial cards to show per carousel slide based on the viewport width.
 * @returns {number} The number of items per slide.
 */
function getItemsPerSlide() {
  if (window.innerWidth < 768) {
    return 1; // On mobile screens, show 1 testimonial per slide
  }
  if (window.innerWidth < 992) {
    return 2; // On tablet screens, show 2 testimonials per slide
  }
  return 3; // On desktop screens, show 3 testimonials per slide
}

/**
 * Generates the testimonial carousel slides and indicators dynamically.
 * It adjusts the number of items per slide based on screen size for responsiveness.
 */
function generateTestimonials() {
  const container = document.getElementById("carouselTestimonialsContainer");
  const indicatorsContainer = document.querySelector(
    "#testimonialCarousel .carousel-indicators"
  );

  // If the containers don't exist on the page, exit the function.
  if (!container || !indicatorsContainer) {
    console.error("Testimonial container or indicators not found!");
    return;
  }

  // Clear previous content
  container.innerHTML = "";
  indicatorsContainer.innerHTML = "";

  const perSlide = getItemsPerSlide();
  const numSlides = Math.ceil(testimonials.length / perSlide);

  // --- Generate Slides and Cards ---
  for (let i = 0; i < testimonials.length; i += perSlide) {
    const slideItems = testimonials.slice(i, i + perSlide);
    const slideIndex = Math.floor(i / perSlide);
    const isActive = slideIndex === 0 ? "active" : "";

    // The `rowItems` will hold the HTML for the cards in the current slide.
    // Bootstrap grid classes (col-md-6, col-lg-4) are used to control the layout.
    // - On large screens (>=992px), 3 cards will appear (col-lg-4).
    // - On medium screens (>=768px), 2 cards will appear (col-md-6).
    // - On small screens (<768px), 1 card will appear (default stacking).
    const rowItems = slideItems
      .map(
        (t) => `
      <div class="col-md-6 col-lg-4 mb-4 d-flex">
        <div class="testimonial-card h-100 w-100">
          <div class="testimonial-quote">"</div>
          <p class="testimonial-content">${t.content}</p>
          <div class="testimonial-author mt-auto">
            <div class="testimonial-info">
              <h5>${t.name}</h5>
              <p>${t.role}</p>
            </div>
          </div>
        </div>
      </div>
    `
      )
      .join("");

    // Add the completed slide to the carousel inner container
    container.innerHTML += `
      <div class="carousel-item ${isActive}">
        <div class="row justify-content-center px-4">${rowItems}</div>
      </div>
    `;
  }

  // --- Generate Indicators ---
  for (let i = 0; i < numSlides; i++) {
    const isActive = i === 0 ? "active" : "";
    const ariaCurrent = i === 0 ? 'aria-current="true"' : "";
    indicatorsContainer.innerHTML += `
      <button
        type="button"
        data-bs-target="#testimonialCarousel"
        data-bs-slide-to="${i}"
        class="${isActive}"
        ${ariaCurrent}
        aria-label="Slide ${i + 1}"
      ></button>
    `;
  }
}

// Generate the testimonials when the page loads
window.addEventListener("DOMContentLoaded", generateTestimonials);

// Regenerate the testimonials when the window is resized to ensure responsiveness
window.addEventListener("resize", generateTestimonials);
