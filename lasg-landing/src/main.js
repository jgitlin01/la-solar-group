import './style.css';

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

/* ── CANVAS SCROLL ANIMATION ── */
const canvas = document.getElementById('hero-canvas');
const ctx = canvas.getContext('2d');

const TOTAL_FRAMES = 60;
const frames = [];
let imagesLoaded = 0;

function frameUrl(n) {
  return `/frames/frame_${String(n).padStart(4, '0')}.jpg`;
}

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  if (frames[currentFrame]?.complete) drawFrame(currentFrame);
}

let currentFrame = 0;

function drawFrame(index) {
  const img = frames[index];
  if (!img || !img.complete) return;

  const cw = canvas.width;
  const ch = canvas.height;
  const iw = img.naturalWidth || 1280;
  const ih = img.naturalHeight || 720;

  const scale = Math.max(cw / iw, ch / ih);
  const dw = iw * scale;
  const dh = ih * scale;
  const dx = (cw - dw) / 2;
  const dy = (ch - dh) / 2;

  ctx.clearRect(0, 0, cw, ch);
  ctx.drawImage(img, dx, dy, dw, dh);

  /* subtle dark vignette overlay to blend into black bg */
  const grad = ctx.createRadialGradient(cw / 2, ch / 2, ch * 0.3, cw / 2, ch / 2, ch * 0.85);
  grad.addColorStop(0, 'rgba(0,0,0,0)');
  grad.addColorStop(1, 'rgba(0,0,0,0.55)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, cw, ch);

  /* bottom fade to black — seamless blend */
  const bottomFade = ctx.createLinearGradient(0, ch * 0.6, 0, ch);
  bottomFade.addColorStop(0, 'rgba(0,0,0,0)');
  bottomFade.addColorStop(1, 'rgba(0,0,0,1)');
  ctx.fillStyle = bottomFade;
  ctx.fillRect(0, ch * 0.6, cw, ch * 0.4);
}

function loadFrames() {
  for (let i = 1; i <= TOTAL_FRAMES; i++) {
    const img = new Image();
    img.src = frameUrl(i);
    img.onload = () => {
      imagesLoaded++;
      if (imagesLoaded === 1) {
        resize();
        drawFrame(0);
      }
    };
    frames.push(img);
  }
}

ScrollTrigger.create({
  trigger: '#hero',
  start: 'top top',
  end: 'bottom bottom',
  scrub: 1,
  onUpdate: (self) => {
    const frameIndex = Math.min(
      Math.floor(self.progress * (TOTAL_FRAMES - 1)),
      TOTAL_FRAMES - 1
    );
    if (frameIndex !== currentFrame) {
      currentFrame = frameIndex;
      drawFrame(currentFrame);
    }
  },
});

window.addEventListener('resize', resize);
loadFrames();
resize();

/* ── NAVBAR SCROLL STATE ── */
const navbar = document.getElementById('navbar');
ScrollTrigger.create({
  start: 'top -80',
  onUpdate: (self) => {
    navbar.classList.toggle('scrolled', self.scroll() > 80);
  },
});

/* ── SCROLL HINT FADE OUT ── */
gsap.to('.scroll-hint', {
  opacity: 0,
  scrollTrigger: {
    trigger: '#hero',
    start: '10% top',
    end: '20% top',
    scrub: true,
  },
});

/* ── STATS COUNTER ANIMATION ── */
const statNums = document.querySelectorAll('.stat-num');

statNums.forEach((el) => {
  const target = parseInt(el.dataset.target, 10);
  ScrollTrigger.create({
    trigger: el.closest('.stat'),
    start: 'top 85%',
    once: true,
    onEnter: () => {
      gsap.fromTo(
        el,
        { textContent: 0 },
        {
          textContent: target,
          duration: 2,
          ease: 'power2.out',
          snap: { textContent: 1 },
          onUpdate() {
            el.textContent = Math.round(parseFloat(el.textContent)).toLocaleString();
          },
        }
      );
    },
  });
});

/* ── GENERIC REVEAL ON SCROLL ── */
function setupReveal(selector, extraDelay = 0) {
  document.querySelectorAll(selector).forEach((el, i) => {
    ScrollTrigger.create({
      trigger: el,
      start: 'top 88%',
      once: true,
      onEnter: () => {
        el.style.animationDelay = `${i * 0.1 + extraDelay}s`;
        el.classList.add('visible');
      },
    });
  });
}

setupReveal('[data-reveal]');
setupReveal('.benefit-card');
setupReveal('.process-step', 0.05);
setupReveal('.process-connector', 0.08);
setupReveal('.offer-text', 0);
setupReveal('.offer-cta', 0.1);
setupReveal('.form-left', 0);
setupReveal('.form-right', 0.1);

/* ── SMOOTH SCROLL FOR CTA LINKS ── */
document.querySelectorAll('a[href="#form"]').forEach((link) => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    gsap.to(window, {
      scrollTo: { y: '#form', offsetY: 80 },
      duration: 1.2,
      ease: 'power3.inOut',
    });
  });
});

/* ── FORM HANDLING ── */
const form = document.getElementById('solar-form');
if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const btn = form.querySelector('.form-submit');
    btn.textContent = 'Sending…';
    btn.disabled = true;

    /* Simulate submission — replace with actual GHL webhook/API call */
    setTimeout(() => {
      btn.textContent = '✓ Request Received!';
      btn.style.background = '#2ea843';
      form.querySelectorAll('input').forEach((inp) => (inp.value = ''));
    }, 1200);
  });

  /* Phone formatting */
  const phoneInput = document.getElementById('phone');
  if (phoneInput) {
    phoneInput.addEventListener('input', (e) => {
      const raw = e.target.value.replace(/\D/g, '').slice(0, 10);
      if (raw.length <= 3) e.target.value = raw;
      else if (raw.length <= 6) e.target.value = `(${raw.slice(0, 3)}) ${raw.slice(3)}`;
      else e.target.value = `(${raw.slice(0, 3)}) ${raw.slice(3, 6)}-${raw.slice(6)}`;
    });
  }
}

/* ── GHL IFRAME: show iframe if form ID has been replaced ── */
(function activateGHLIframe() {
  const iframe = document.getElementById('ghl-form-iframe');
  const fallback = document.querySelector('.fallback-form');
  if (iframe && !iframe.src.includes('REPLACE_WITH_YOUR_FORM_ID')) {
    iframe.style.display = 'block';
    iframe.style.height = '520px';
    if (fallback) fallback.style.display = 'none';

    /* load GHL embed script */
    const s = document.createElement('script');
    s.src = 'https://link.msgsndr.com/js/form_embed.js';
    document.body.appendChild(s);
  }
})();
