// ── Shared state (read/written by editor.js, slideshow.js, pdf.js) ───────────
var currentMarkdown = '';
var currentMode = 'slideshow';

// ── Utilities ─────────────────────────────────────────────────────────────────

function showToast(msg, duration) {
  duration = duration || 2200;
  var toast = document.getElementById('toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add('show');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(function () { toast.classList.remove('show'); }, duration);
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  var d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ── Mode switching ─────────────────────────────────────────────────────────────

function applyMode(mode) {
  ['edit', 'slideshow', 'pdf', 'meta'].forEach(function (m) {
    var tab = document.getElementById('tab-' + m);
    var panel = document.getElementById('mode-' + m);
    if (tab) tab.classList.toggle('active', m === mode);
    if (panel) panel.classList.toggle('hidden', m !== mode);
  });
}

function switchMode(mode) {
  if (mode === currentMode) return;

  // Capture editor content before leaving edit mode
  if (typeof editorReady !== 'undefined' && editorReady && typeof editor !== 'undefined' && editor) {
    currentMarkdown = editor.getValue();
  }

  // Turn off laser when leaving slideshow
  if (currentMode === 'slideshow' && typeof laserOn !== 'undefined' && laserOn) {
    if (typeof setLaser === 'function') setLaser(false);
  }

  currentMode = mode;
  applyMode(mode);

  if (mode === 'edit') {
    if (typeof ensureEditor === 'function') ensureEditor();
    setTimeout(function () {
      if (typeof editor !== 'undefined' && editor) {
        editor.refresh();
        editor.focus();
      }
      if (typeof previewOpen !== 'undefined' && !previewOpen) {
        if (typeof togglePreview === 'function') togglePreview();
      } else {
        if (typeof renderPreview === 'function') renderPreview();
      }
    }, 30);
  } else if (mode === 'slideshow') {
    // On mobile, auto-request fullscreen for immersive presenting
    if (window.innerWidth <= 768) {
      var el = document.getElementById('mode-slideshow');
      if (el && el.requestFullscreen) {
        el.requestFullscreen().catch(function () {});
      }
    }
    if (typeof renderSlideshow === 'function') renderSlideshow();
  } else if (mode === 'pdf') {
    if (typeof renderPdf === 'function') renderPdf();
  }
}
