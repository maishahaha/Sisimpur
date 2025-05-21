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

function generateTestimonials() {
  const container = document.getElementById("carouselTestimonialsContainer");
  container.innerHTML = "";

  const isMobile = window.innerWidth < 768;
  const perSlide = isMobile ? 1 : 3;

  for (let i = 0; i < testimonials.length; i += perSlide) {
    const slideItems = testimonials.slice(i, i + perSlide);
    const isActive = i === 0 ? "active" : "";

    const row = slideItems
      .map(
        (t) => `
      <div class="col-md-4 mb-4">
        <div class="testimonial-card h-100">
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
    `,
      )
      .join("");

    container.innerHTML += `
      <div class="carousel-item ${isActive}">
        <div class="row justify-content-center">${row}</div>
      </div>
    `;
  }
}

window.addEventListener("DOMContentLoaded", generateTestimonials);
window.addEventListener("resize", generateTestimonials);
