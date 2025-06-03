// SpyBoy style JS — minimal but ready for future hacking effects
document.addEventListener("DOMContentLoaded", () => {
  console.log("VillenSec - SpyBoy style loaded ⚡");
  // Example: Add flicker effect on nav brand on hover
  const brand = document.querySelector('.navbar-brand');
  brand?.addEventListener('mouseenter', () => {
    brand.classList.add('glitch-text');
  });
  brand?.addEventListener('mouseleave', () => {
    brand.classList.remove('glitch-text');
  });
});
