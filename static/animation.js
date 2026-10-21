// ─── Observer Options ─────────────────────────────────────────────────────────
const observerOptions = { threshold: 0.3 };

// ─── Zoom-in for Service Cards ────────────────────────────────────────────────
document.querySelectorAll(".service-card").forEach(card => {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => card.classList.toggle("zoom-in", e.isIntersecting));
  }, observerOptions);
  card.classList.add("pre-zoom");
  obs.observe(card);
});

// ─── Pop-in for Gallery Images ────────────────────────────────────────────────
document.querySelectorAll(".gallery-grid img").forEach(img => {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => img.classList.toggle("pop-in", e.isIntersecting));
  }, observerOptions);
  img.classList.add("pre-pop");
  obs.observe(img);
});

// ─── Slide-in for Pricing Cards ───────────────────────────────────────────────
document.querySelectorAll(".pricing-card").forEach(card => {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => card.classList.toggle("slide-in", e.isIntersecting));
  }, observerOptions);
  card.classList.add("pre-slide");
  obs.observe(card);
});

// ─── Typing Animation (About Us) ──────────────────────────────────────────────
function runTypingAnimation() {
  const lines = [
    "Established with a passion for perfection, we bring timeless detail to every vehicle. Our black-and-gold signature offers unmatched luxury and a bold first impression.",
    "Expert technicians, premium products, and individualized attention for each client. We pride ourselves on our meticulous approach and flawless results, inspired by the world’s elite automotive experiences.",
    "Experience the difference—where every detail matters and craftsmanship meets prestige."
  ];
  const target = document.getElementById("about-typed");
  if (!target) return;

  target.innerHTML = "";
  let lineIndex = 0, charIndex = 0;
  const typingSpeed = 22, linePause = 700;

  function typeLine() {
    if (lineIndex < lines.length) {
      let p = target.querySelector(`p[data-line='${lineIndex}']`);
      if (!p) {
        p = document.createElement('p');
        p.setAttribute('data-line', lineIndex);
        p.style.marginBottom = '14px';
        target.appendChild(p);
      }
      p.innerHTML = lines[lineIndex].slice(0, charIndex + 1) + '<span class="typing-cursor">|</span>';
      if (charIndex < lines[lineIndex].length - 1) {
        charIndex++;
        setTimeout(typeLine, typingSpeed);
      } else {
        p.innerHTML = lines[lineIndex];
        lineIndex++;
        charIndex = 0;
        setTimeout(typeLine, linePause);
      }
    }
  }

  typeLine();
}

// ─── “Run Once” Wrapper ───────────────────────────────────────────────────────
let typingStarted = false;
function startTypingOnce() {
  if (typingStarted) return;
  typingStarted = true;
  const aboutContainer = document.getElementById('about-typed');
  if (aboutContainer) aboutContainer.style.opacity = '1';
  runTypingAnimation();
}

// ─── DOMContentLoaded: Popup + Typing Trigger ────────────────────────────────
document.addEventListener("DOMContentLoaded", function () {
  const aboutContainer = document.getElementById('about-typed');
  if (aboutContainer) {
    aboutContainer.style.opacity = '0';
    aboutContainer.style.transition = 'opacity 0.3s ease';
  }

  const modal       = document.getElementById('terms-modal');
  const scrollbox   = document.getElementById('terms-scrollbox');
  const agreeBtn    = document.getElementById('agree-btn');
  const disagreeBtn = document.getElementById('disagree-btn');

  if (!(modal && scrollbox && agreeBtn && disagreeBtn)) return;

  // Show modal if not agreed yet
  if (!localStorage.getItem('agreedToTerms')) {
    modal.style.display = 'flex';

    const scrollY = window.scrollY;
    document.body.style.position = 'fixed';
    document.body.style.top = `-${scrollY}px`;
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.width = '100%';
    document.body.style.overflow = 'hidden';
    document.body.setAttribute('data-scroll-lock', scrollY);
    document.body.classList.add('modal-open');  // ✅ added fix
  } else {
    startTypingOnce();
  }

  // Enable Agree button only after scroll
  scrollbox.addEventListener('scroll', () => {
    const atBottom = scrollbox.scrollTop + scrollbox.clientHeight >= scrollbox.scrollHeight - 1;
    agreeBtn.disabled = !atBottom;
  });

  // On Agree
  agreeBtn.addEventListener('click', () => {
    localStorage.setItem('agreedToTerms', 'yes');
    modal.style.display = 'none';

    // Restore scroll
    const scrollY = parseInt(document.body.getAttribute('data-scroll-lock') || '0');
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.left = '';
    document.body.style.right = '';
    document.body.style.width = '';
    document.body.style.overflow = '';
    document.body.classList.remove('modal-open'); // ✅ remove class
    document.body.removeAttribute('data-scroll-lock');
    window.scrollTo(0, scrollY);

    startTypingOnce();
  });

  // On Disagree
  disagreeBtn.addEventListener('click', () => {
    scrollbox.innerHTML = "<h3>Access Denied</h3><p>You must agree to the terms to use this website.</p>";
    agreeBtn.style.display = 'none';
    disagreeBtn.style.display = 'none';
  });
});
