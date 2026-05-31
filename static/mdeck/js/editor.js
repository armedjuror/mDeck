// ── Editor state ──────────────────────────────────────────────────────────────
var editor      = null;
var editorReady = false;
var previewOpen = false;
var splitPct    = 50;
var dragging    = false;
var previewTimer = null;
var draftTimer  = null;

// ── CodeMirror init (once) ────────────────────────────────────────────────────

function ensureEditor() {
  if (editorReady) return;
  editorReady = true;

  var textarea = document.getElementById('editor-textarea');
  if (!textarea) return;

  editor = CodeMirror.fromTextArea(textarea, {
    mode: 'markdown',
    theme: 'dracula',
    lineNumbers: true,
    lineWrapping: true,
    autofocus: false,
    indentWithTabs: false,
    tabSize: 2,
    extraKeys: {
      'Ctrl-S': function () { if (typeof saveNote === 'function') saveNote(); },
      'Cmd-S':  function () { if (typeof saveNote === 'function') saveNote(); },
      'Esc': function () { if (typeof switchMode === 'function') switchMode('slideshow'); },
    },
  });

  editor.setValue(currentMarkdown);

  editor.on('change', function () {
    // Live preview debounce
    if (previewOpen) {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(renderPreview, 400);
    }

    // Autosave to server (replace localStorage with POST)
    if (typeof AUTOSAVE_URL !== 'undefined' && AUTOSAVE_URL) {
      clearTimeout(draftTimer);
      draftTimer = setTimeout(function () {
        var content = editor.getValue();
        fetch(AUTOSAVE_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '',
          },
          body: JSON.stringify({ content: content }),
        }).catch(function () {}); // silent fail
      }, 600);
    }
  });

  // ── Scroll sync (slide-aware) ────────────────────────────────────────────────
  var scrollLock = false;

  function getSlideLineRanges() {
    var lines = editor.getValue().split('\n');
    var ranges = [];
    var start = 0;
    for (var i = 0; i < lines.length; i++) {
      if (lines[i].trim() === '---') {
        ranges.push({ start: start, end: i - 1 });
        start = i + 1;
      }
    }
    ranges.push({ start: start, end: lines.length - 1 });
    return ranges;
  }

  editor.on('scroll', function () {
    if (scrollLock || !previewOpen) return;
    var info = editor.getScrollInfo();
    var topLine = editor.lineAtHeight(info.top, 'local');
    var ranges = getSlideLineRanges();
    var slideIdx = 0;
    for (var i = 0; i < ranges.length; i++) {
      if (topLine >= ranges[i].start) slideIdx = i;
      else break;
    }
    var wraps = document.querySelectorAll('#split-preview .sp-wrap');
    var preview = document.getElementById('split-preview');
    if (!wraps.length || slideIdx >= wraps.length) return;
    var wrap = wraps[slideIdx];
    var targetTop = wrap.getBoundingClientRect().top
      - preview.getBoundingClientRect().top
      + preview.scrollTop;
    scrollLock = true;
    preview.scrollTo({ top: targetTop, behavior: 'smooth' });
    setTimeout(function () { scrollLock = false; }, 300);
  });

  var splitPreviewEl = document.getElementById('split-preview');
  if (splitPreviewEl) {
    splitPreviewEl.addEventListener('scroll', function () {
      if (scrollLock || !previewOpen) return;
      var preview = this;
      var wraps = preview.querySelectorAll('.sp-wrap');
      if (!wraps.length) return;
      var previewTop = preview.getBoundingClientRect().top;
      var slideIdx = 0;
      var minDist = Infinity;
      for (var i = 0; i < wraps.length; i++) {
        var dist = Math.abs(wraps[i].getBoundingClientRect().top - previewTop);
        if (dist < minDist) { minDist = dist; slideIdx = i; }
      }
      var ranges = getSlideLineRanges();
      if (slideIdx >= ranges.length) return;
      var coords = editor.charCoords({ line: ranges[slideIdx].start, ch: 0 }, 'local');
      scrollLock = true;
      editor.getScrollerElement().scrollTo({ top: coords.top, behavior: 'smooth' });
      setTimeout(function () { scrollLock = false; }, 300);
    });
  }
}

// ── Preview toggle ─────────────────────────────────────────────────────────────

function togglePreview() {
  previewOpen = !previewOpen;
  var divider  = document.getElementById('split-divider');
  var pane     = document.getElementById('split-preview-pane');
  var btn      = document.getElementById('btn-preview-toggle');
  var epane    = document.getElementById('editor-pane');

  if (previewOpen) {
    if (divider) divider.classList.remove('hidden');
    if (pane) pane.classList.remove('hidden');
    if (epane) epane.style.flex = '0 0 ' + splitPct + '%';
    if (btn) { btn.classList.add('active'); btn.textContent = '\u229f Preview'; }
    renderPreview();
  } else {
    if (divider) divider.classList.add('hidden');
    if (pane) pane.classList.add('hidden');
    if (epane) epane.style.flex = '';
    if (btn) { btn.classList.remove('active'); btn.textContent = '\u229e Preview'; }
  }
  setTimeout(function () { if (editor) editor.refresh(); }, 30);
}

// ── Preview rendering (scale-down of real 960×700 slide) ─────────────────────

function renderPreview() {
  if (typeof setupMarked === 'function') setupMarked();
  var md = (editorReady && editor) ? editor.getValue() : currentMarkdown;
  var slides = splitSlides(md);
  var container = document.getElementById('split-preview');
  if (!container) return;
  container.innerHTML = slides.map(function (s, i) {
    return '<div class="sp-wrap">' +
      '<div class="sp-num">Slide ' + (i + 1) + ' / ' + slides.length + '</div>' +
      '<div class="sp-outer">' +
        '<div class="sp-scale-wrap">' +
          '<div class="sp-slide">' + renderMd(s) + '</div>' +
        '</div>' +
      '</div>' +
    '</div>';
  }).join('');
  scalePreviewSlides();
}

function scalePreviewSlides() {
  document.querySelectorAll('.sp-outer').forEach(function (outer) {
    var w = outer.offsetWidth;
    if (!w) return;
    var wrap = outer.querySelector('.sp-scale-wrap');
    if (wrap) wrap.style.transform = 'scale(' + (w / 960) + ')';
  });
}

// ── Save & download ───────────────────────────────────────────────────────────

function saveNote() {
  if (!editorReady || !editor) {
    if (typeof ensureEditor === 'function') ensureEditor();
    setTimeout(saveNote, 60);
    return;
  }
  var content = editor.getValue();
  currentMarkdown = content;

  if (typeof SAVE_URL !== 'undefined' && SAVE_URL) {
    // Django mode: POST to server, then trigger download
    var btn = document.querySelector('.btn-save');
    if (btn) btn.disabled = true;

    fetch(SAVE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': typeof CSRF_TOKEN !== 'undefined' ? CSRF_TOKEN : '',
      },
      body: JSON.stringify({ content: content }),
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.ok) {
        _triggerDownload(content, (typeof DECK_SLUG !== 'undefined' ? DECK_SLUG : 'deck') + '.md');
        showToast('Saved & downloaded');
      } else {
        showToast('Save failed');
      }
    })
    .catch(function () { showToast('Save failed'); })
    .finally(function () {
      if (btn) btn.disabled = false;
    });
  } else {
    // Fallback: download only (no server)
    _triggerDownload(content, 'deck.md');
    showToast('Downloaded');
  }
}

function _triggerDownload(content, filename) {
  var url = URL.createObjectURL(new Blob([content], { type: 'text/markdown;charset=utf-8' }));
  var a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}

// ── DOM listeners (set up after DOM ready) ────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  // Draggable divider
  var dividerEl = document.getElementById('split-divider');
  if (dividerEl) {
    dividerEl.addEventListener('mousedown', function (e) {
      dragging = true;
      dividerEl.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });
  }

  document.addEventListener('mousemove', function (e) {
    if (!dragging) return;
    var modeEdit = document.getElementById('mode-edit');
    if (!modeEdit) return;
    var rect = modeEdit.getBoundingClientRect();
    splitPct = Math.max(20, Math.min(80, ((e.clientX - rect.left) / rect.width) * 100));
    var epane = document.getElementById('editor-pane');
    if (epane) epane.style.flex = '0 0 ' + splitPct + '%';
    if (editor) editor.refresh();
    scalePreviewSlides();
  });

  document.addEventListener('mouseup', function () {
    if (!dragging) return;
    dragging = false;
    var dividerEl = document.getElementById('split-divider');
    if (dividerEl) dividerEl.classList.remove('dragging');
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    if (editor) editor.refresh();
  });

  // Preview resize
  window.addEventListener('resize', function () {
    if (previewOpen) scalePreviewSlides();
  });

  // Mobile: hide preview by default, toggle as drawer
  if (window.innerWidth <= 768) {
    var previewPane = document.getElementById('split-preview-pane');
    if (previewPane) {
      previewPane.classList.add('mobile-drawer');
    }
  }
});
