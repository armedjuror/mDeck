// ── Slideshow state ───────────────────────────────────────────────────────────
var revealInst  = null;
var revealReady = false;
var laserOn     = false;

// ── Colour helpers ─────────────────────────────────────────────────────────────

function _hexToRgba(hex, alpha) {
  hex = (hex || '').replace('#', '');
  if (hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
  var r = parseInt(hex.slice(0,2),16) || 0;
  var g = parseInt(hex.slice(2,4),16) || 0;
  var b = parseInt(hex.slice(4,6),16) || 0;
  return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
}

function _computeBg(cfg) {
  var base = cfg.bgGradient || cfg.bg;
  var tint = cfg.ruleColor || cfg.text || '#e0e0e0';
  if (cfg.surface === 'dots') {
    var dot = _hexToRgba(tint, 0.08);
    return 'radial-gradient(circle,' + dot + ' 1px,transparent 1px) 0 0/24px 24px,' + base;
  }
  if (cfg.surface === 'rules') {
    var rule = _hexToRgba(tint, 0.06);
    return 'repeating-linear-gradient(to bottom,transparent,transparent 39px,' + rule + ' 39px,' + rule + ' 40px),' + base;
  }
  return base;
}

// ── Reveal.js init ────────────────────────────────────────────────────────────

function renderSlideshow() {
  if (typeof setupMarked === 'function') setupMarked();
  var slides = splitSlidesWithConfig(currentMarkdown);
  var slidesEl = document.getElementById('reveal-slides');
  if (!slidesEl) return;

  var cfg = (typeof DECK_CONFIG !== 'undefined') ? DECK_CONFIG : {};

  slidesEl.innerHTML = slides.map(function (s) {
    var html = renderMd(s.content);
    // reveal: incremental — add fragment class to every top-level <li>
    if (s.config.reveal === 'incremental') {
      html = html.replace(/<li>/g, '<li class="fragment">');
    }
    var attrs = '';
    if (s.config.bg) {
      attrs += ' data-background-image="' + s.config.bg.replace(/"/g, '&quot;') + '"';
      attrs += ' data-background-opacity="0.55"';
    }
    return '<section' + attrs + '>' + html + '</section>';
  }).join('');

  if (!revealReady) {
    revealReady = true;
    var container = document.querySelector('#mode-slideshow .reveal');
    if (!container) {
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
