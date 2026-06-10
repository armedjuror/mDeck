// ── Slideshow state ───────────────────────────────────────────────────────────
var revealInst  = null;
var revealReady = false;
var laserOn     = false;

// ── Reveal.js init ────────────────────────────────────────────────────────────

function renderSlideshow() {
  if (typeof setupMarked === 'function') setupMarked();
  var slides = splitSlides(currentMarkdown);
  var slidesEl = document.getElementById('reveal-slides');
  if (!slidesEl) return;

  slidesEl.innerHTML = slides.map(function (s) {
    return '<section>' + renderMd(s) + '</section>';
  }).join('');

  if (!revealReady) {
    revealReady = true;
    var container = document.querySelector('#mode-slideshow .reveal');
    if (!container) {
      // deck_present.html: reveal is directly in body
      container = document.querySelector('.reveal-container .reveal');
    }
    if (!container) return;
    revealInst = new Reveal(container, {
      hash: false,
      transition: 'fade',
      backgroundTransition: 'fade',
      center: true,
      controls: true,
      progress: true,
      slideNumber: 'c/t',
      keyboard: true,
      overview: true,
      embedded: true,
      touch: true,
      margin: 0.08,
      width: 960,
      height: 700,
    });
    revealInst.initialize().then(function () {
      revealInst.layout();
      if (typeof window.onRevealReady === 'function') window.onRevealReady(revealInst);
      // Second layout after fonts/theme styles settle
      setTimeout(function () { revealInst.layout(); }, 250);
    });
  } else {
    revealInst.sync();
    revealInst.layout();
    revealInst.slide(0);
  }
}

// ── Fullscreen ─────────────────────────────────────────────────────────────────

window.toggleFullscreen = function () {
  var el = document.getElementById('mode-slideshow') || document.querySelector('.reveal-container');
  if (!el) return;
  if (document.fullscreenElement) {
    document.exitFullscreen();
  } else {
    el.requestFullscreen().catch(function () {});
  }
};

document.addEventListener('fullscreenchange', function () {
  var btn = document.getElementById('btn-fullscreen');
  var isFs = !!document.fullscreenElement;
  if (btn) {
    btn.textContent = isFs ? '\u2715 Exit Full' : '\u26f6 Fullscreen';
    btn.classList.toggle('active', isFs);
  }
  if (revealInst) setTimeout(function () { revealInst.layout(); }, 50);
});

// ── Laser pointer ─────────────────────────────────────────────────────────────

function setLaser(on) {
  laserOn = on;
  var dot = document.getElementById('laser-dot');
  var btn = document.getElementById('btn-laser');
  var ss  = document.getElementById('mode-slideshow');
  if (dot) dot.classList.toggle('hidden', !on);
  if (btn) btn.classList.toggle('active', on);
  if (ss) ss.style.cursor = on ? 'none' : '';
}

window.toggleLaser = function () { setLaser(!laserOn); };

document.addEventListener('mousemove', function (e) {
  if (!laserOn) return;
  var dot = document.getElementById('laser-dot');
  if (!dot) return;
  dot.style.left = e.clientX + 'px';
  dot.style.top  = e.clientY + 'px';
});

// ── Layout on resize ─────────────────────────────────────────────────────────

window.addEventListener('resize', function () {
  if (revealInst && typeof currentMode !== 'undefined' && currentMode === 'slideshow') {
    revealInst.layout();
  }
});
