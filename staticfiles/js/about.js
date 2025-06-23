(function () {
  'use strict';

  // Typewriter Effect
  const aboutText = "I'm not just a student — I'm a storyteller in binary, a defender of code, and a lover who writes code like Shayari. From the dusty classrooms of Bihar to the code labs of DU, I’m Villen Bhai — coding emotions, building the future.";
  const textElement = document.querySelector('#dynamic-about-text');
  if (textElement) {
    let index = 0;
    function typewriter() {
      if (index < aboutText.length) {
        textElement.textContent = textElement.textContent.slice(0, -1) + aboutText.charAt(index) + '|';
        index++;
        setTimeout(typewriter, 40);
      } else {
        textElement.textContent = aboutText;
      }
    }
    typewriter();
  }

  // Video Toggle
  const video = document.querySelector('.video-bg');
  const toggleBtn = document.querySelector('#video-toggle');
  if (video && toggleBtn) {
    let paused = false;
    video.play().catch((error) => {
      console.log('Autoplay failed:', error);
      document.addEventListener('click', () => {
        if (!paused) video.play().catch((err) => console.log('Manual play failed:', err));
      }, { once: true });
    });

    toggleBtn.addEventListener('click', () => {
      if (paused) {
        video.play().catch((err) => console.log('Play failed:', err));
        toggleBtn.innerHTML = '⏸️ Pause';
        toggleBtn.setAttribute('aria-label', 'Pause video playback');
      } else {
        video.pause();
        toggleBtn.innerHTML = '▶️ Play';
        toggleBtn.setAttribute('aria-label', 'Play video playback');
      }
      paused = !paused;
    });

    toggleBtn.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        toggleBtn.click();
      }
    });
  }

  // Education Card Animation
  const cards = document.querySelectorAll('.education-card');
  cards.forEach((card, index) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, index * 200);
  });

  // Carousel
  const carousel = document.querySelector('#carousel');
  const dots = document.querySelectorAll('.dot');
  const prevBtn = document.querySelector('.carousel-prev');
  const nextBtn = document.querySelector('.carousel-next');
  if (carousel && dots.length && prevBtn && nextBtn) {
    let currentSlide = 0;
    const totalSlides = document.querySelectorAll('.slide').length;

    function moveToSlide(index) {
      carousel.style.transform = `translateX(-${index * 100}%)`;
      dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === index);
        dot.setAttribute('aria-selected', i === index ? 'true' : 'false');
      });
      currentSlide = index;
    }

    dots.forEach((dot, i) => {
      dot.addEventListener('click', () => moveToSlide(i));
      dot.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          moveToSlide(i);
        }
      });
    });

    prevBtn.addEventListener('click', () => moveToSlide((currentSlide - 1 + totalSlides) % totalSlides));
    nextBtn.addEventListener('click', () => moveToSlide((currentSlide + 1) % totalSlides));

    [prevBtn, nextBtn].forEach(btn => {
      btn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          btn.click();
        }
      });
    });
  }
})();