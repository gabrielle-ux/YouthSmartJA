// ===============================
// MOBILE NAVIGATION
// ===============================
const navToggle = document.querySelector(".nav-toggle");
const navLinks = document.querySelector(".nav-links");

if (navToggle) {
  navToggle.addEventListener("click", () => {
    navLinks.classList.toggle("open");
  });
}

// Close menu when clicking links
document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("open");
  });
});


// ===============================
// SCROLL REVEAL ANIMATION
// ===============================
const revealElements = document.querySelectorAll(".reveal");

function revealOnScroll() {
  const triggerBottom = window.innerHeight * 0.85;

  revealElements.forEach(el => {
    const rect = el.getBoundingClientRect();

    if (rect.top < triggerBottom) {
      el.classList.add("in");
    }
  });
}

window.addEventListener("scroll", revealOnScroll);
window.addEventListener("load", revealOnScroll);


// ===============================
// ACTIVE NAVIGATION LINK
// ===============================
const sections = document.querySelectorAll("section[id]");
const navItems = document.querySelectorAll(".nav-links a");

function activateNavLink() {
  let currentSection = "";

  sections.forEach(section => {
    const sectionTop = section.offsetTop - 200;
    const sectionHeight = section.offsetHeight;

    if (
      window.scrollY >= sectionTop &&
      window.scrollY < sectionTop + sectionHeight
    ) {
      currentSection = section.getAttribute("id");
    }
  });

  navItems.forEach(link => {
    link.classList.remove("active");

    if (link.getAttribute("href") === `#${currentSection}`) {
      link.classList.add("active");
    }
  });
}

window.addEventListener("scroll", activateNavLink);


// ===============================
// ANIMATED PROGRESS BARS
// ===============================
const bars = document.querySelectorAll(".bar-fill");

function animateBars() {
  bars.forEach(bar => {
    const rect = bar.getBoundingClientRect();

    if (
      rect.top < window.innerHeight - 50 &&
      !bar.classList.contains("animated")
    ) {
      bar.classList.add("animated");

      // FIXED ATTRIBUTE NAME
      const width = bar.dataset.w;

      bar.style.width = width + "%";
    }
  });
}

window.addEventListener("scroll", animateBars);
window.addEventListener("load", animateBars);


// ===============================
// PARALLAX BLOBS
// ===============================
const blobs = document.querySelectorAll(".blob");

window.addEventListener("mousemove", e => {
  const x = e.clientX / window.innerWidth;
  const y = e.clientY / window.innerHeight;

  blobs.forEach((blob, index) => {
    const speed = (index + 1) * 20;

    blob.style.transform = `
      translate(
        ${(x - 0.5) * speed}px,
        ${(y - 0.5) * speed}px
      )
    `;
  });
});


// ===============================
// FLOATING CARD EFFECT
// ===============================
const interactiveCards = document.querySelectorAll(
  ".card, .feature, .roadmap-col, .step"
);

interactiveCards.forEach(card => {
  card.addEventListener("mousemove", e => {
    const rect = card.getBoundingClientRect();

    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -4;
    const rotateY = ((x - centerX) / centerX) * 4;

    card.style.transform = `
      perspective(1000px)
      rotateX(${rotateX}deg)
      rotateY(${rotateY}deg)
      translateY(-5px)
    `;
  });

  card.addEventListener("mouseleave", () => {
    card.style.transform = `
      perspective(1000px)
      rotateX(0deg)
      rotateY(0deg)
      translateY(0)
    `;
  });
});


// ===============================
// BACK TO TOP BUTTON
// ===============================
const topBtn = document.createElement("button");

topBtn.innerHTML = "↑";
topBtn.classList.add("top-btn");

document.body.appendChild(topBtn);

// Button styling
Object.assign(topBtn.style, {
  position: "fixed",
  bottom: "20px",
  right: "20px",
  width: "50px",
  height: "50px",
  borderRadius: "50%",
  border: "none",
  background: "linear-gradient(135deg,#2dc4b3,#1ea899)",
  color: "#0f1a1f",
  fontSize: "1.2rem",
  fontWeight: "bold",
  cursor: "pointer",
  opacity: "0",
  pointerEvents: "none",
  transition: "all .3s ease",
  zIndex: "9999",
  boxShadow: "0 8px 32px -8px rgba(0,0,0,.4)"
});

// Show/hide button
window.addEventListener("scroll", () => {
  if (window.scrollY > 500) {
    topBtn.style.opacity = "1";
    topBtn.style.pointerEvents = "auto";
  } else {
    topBtn.style.opacity = "0";
    topBtn.style.pointerEvents = "none";
  }
});

// Scroll to top
topBtn.addEventListener("click", () => {
  window.scrollTo({
    top: 0,
    behavior: "smooth"
  });
});


// ===============================
// HERO TITLE GLOW EFFECT
// ===============================
const heroTitle = document.querySelector(".hero h1");

if (heroTitle) {
  window.addEventListener("mousemove", e => {
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;

    heroTitle.style.textShadow = `
      ${x}px ${y}px 40px rgba(45,196,179,.25)
    `;
  });
}


// ===============================
// SMOOTH SECTION FADE-IN
// ===============================
const observer = new IntersectionObserver(
  entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
      }
    });
  },
  {
    threshold: 0.15
  }
);

document.querySelectorAll(".reveal").forEach(el => {
  observer.observe(el);
});
