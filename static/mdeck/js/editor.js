// ── Editor state ──────────────────────────────────────────────────────────────
var editor      = null;
var editorReady = false;
var previewOpen = false;
var splitPct    = 50;
var dragging    = false;
var previewTimer  = null;
var draftTimer    = null;
var latexErrTimer = null;
var latexMarks    = [];

// ── Find & Replace ────────────────────────────────────────────────────────────
var frpMarks      = [];
var frpMatches    = [];
var frpCurrentIdx = -1;

function openFindReplace() {
  if (!editorReady) return;
  var panel = document.getElementById('find-replace-panel');
  if (!panel) {
    panel = buildFrpPanel();
  }
  panel.style.display = 'flex';
  var findInput = document.getElementById('frp-find');
  var sel = editor.getSelection();
  if (sel) findInput.value = sel;
  findInput.focus();
  findInput.select();
  frpSearch();
}

function closeFindReplace() {
  var panel = document.getElementById('find-replace-panel');
  if (panel) panel.style.display = 'none';
  frpClearMarks();
  editor.focus();
}

function buildFrpPanel() {
  var panel = document.createElement('div');
  panel.id = 'find-replace-panel';
  panel.innerHTML =
    '<div class="frp-row">' +
      '<input id="frp-find" placeholder="Find\u2026" autocomplete="off" spellcheck="false">' +
      '<span id="frp-count"></span>' +
      '<button class="frp-btn" id="frp-prev" title="Previous (Shift+Enter)">\u2191</button>' +
      '<button class="frp-btn" id="frp-next" title="Next (Enter)">\u2193</button>' +
      '<button class="frp-btn frp-close-btn" id="frp-close">\u2715</button>' +
    '</div>' +
    '<div class="frp-row">' +
      '<input id="frp-replace" placeholder="Replace with\u2026" autocomplete="off" spellcheck="false">' +
      '<button class="frp-btn frp-action-btn" id="frp-replace-one">Replace</button>' +
      '<button class="frp-btn frp-action-btn" id="frp-replace-all">All</button>' +
    '</div>';

  var editorPane = document.getElementById('editor-pane');
  editorPane.insertBefore(panel, editorPane.firstChild);

  document.getElementById('frp-find').addEventListener('input', frpSearch);
  document.getElementById('frp-next').addEventListener('click', function () { frpMove(1); });
  document.getElementById('frp-prev').addEventListener('click', function () { frpMove(-1); });
  document.getElementById('frp-close').addEventListener('click', closeFindReplace);
  document.getElementById('frp-replace-one').addEventListener('click', frpReplaceOne);
  document.getElementById('frp-replace-all').addEventListener('click', frpReplaceAll);

  document.getElementById('frp-find').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); frpMove(e.shiftKey ? -1 : 1); }
    if (e.key === 'Escape') closeFindReplace();
    if ((e.metaKey || e.ctrlKey) && e.key === 'f') { e.preventDefault(); }
  });
  document.getElementById('frp-replace').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') { e.preventDefault(); frpReplaceOne(); }
    if (e.key === 'Escape') closeFindReplace();
  });

  return panel;
}

function frpClearMarks() {
  frpMarks.forEach(function (m) { m.clear(); });
  frpMarks = [];
  frpMatches = [];
  frpCurrentIdx = -1;
}

function frpSearch() {
  frpClearMarks();
  var query = document.getElementById('frp-find').value;
  var countEl = document.getElementById('frp-count');
  if (!query) { countEl.textContent = ''; return; }

  var cursor = editor.getSearchCursor(query, CodeMirror.Pos(0, 0), { caseFold: true });
  while (cursor.findNext()) {
    frpMatches.push({ from: cursor.from(), to: cursor.to() });
    frpMarks.push(editor.markText(cursor.from(), cursor.to(), { className: 'frp-match' }));
  }

  if (frpMatches.length > 0) {
    frpCurrentIdx = 0;
    frpHighlightCurrent();
  } else {
    countEl.textContent = 'No results';
  }
}

function frpHighlightCurrent() {
  frpMarks.forEach(function (m, i) {
    m.clear();
    frpMarks[i] = editor.markText(frpMatches[i].from, frpMatches[i].to, {
      className: i === frpCurrentIdx ? 'frp-match-current' : 'frp-match',
    });
  });
  editor.scrollIntoView(frpMatches[frpCurrentIdx], 80);
  document.getElementById('frp-count').textContent =
    (frpCurrentIdx + 1) + ' / ' + frpMatches.length;
}

function frpMove(dir) {
  if (!frpMatches.length) return;
  frpCurrentIdx = (frpCurrentIdx + dir + frpMatches.length) % frpMatches.length;
  frpHighlightCurrent();
}

function frpReplaceOne() {
  if (!frpMatches.length || frpCurrentIdx < 0) return;
  var m = frpMatches[frpCurrentIdx];
  editor.replaceRange(document.getElementById('frp-replace').value, m.from, m.to);
  frpSearch();
}

function frpReplaceAll() {
  var query = document.getElementById('frp-find').value;
  if (!query || !frpMatches.length) return;
  var replacement = document.getElementById('frp-replace').value;
  editor.operation(function () {
    var cursor = editor.getSearchCursor(query, CodeMirror.Pos(0, 0), { caseFold: true });
    while (cursor.findNext()) cursor.replace(replacement);
  });
  frpSearch();
}

// Intercept Cmd/Ctrl+F at document level to prevent browser's native find
document.addEventListener('keydown', function (e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
    e.preventDefault();
    openFindReplace();
  }
}, true);

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
      'Ctrl-F': function () { openFindReplace(); },
      'Cmd-F':  function (e) { openFindReplace(); },
      'Esc': function () { if (typeof switchMode === 'function') switchMode('slideshow'); },
    },
  });

  editor.setValue(currentMarkdown);
  setTimeout(checkLatexErrors, 800);

  editor.on('change', function () {
    // Live preview debounce
    if (previewOpen) {
      clearTimeout(previewTimer);
      previewTimer = setTimeout(renderPreview, 400);
    }

    // LaTeX error check debounce
    clearTimeout(latexErrTimer);
    latexErrTimer = setTimeout(checkLatexErrors, 700);

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

// ── LaTeX error checking ──────────────────────────────────────────────────────

function posFromIndex(content, idx) {
  var before = content.substring(0, idx);
  var lines = before.split('\n');
  return { line: lines.length - 1, ch: lines[lines.length - 1].length };
}

function checkLatexErrors() {
  if (!editor || typeof katex === 'undefined') return;

  // Clear previous marks
  latexMarks.forEach(function (m) { m.clear(); });
  latexMarks = [];

  var content = editor.getValue();
  var errors = [];

  // Match $$...$$ (display) first, then $...$ (inline)
  // Use two passes to avoid the inline regex capturing inside display blocks
  var re = /\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$/g;
  var match;

  while ((match = re.exec(content)) !== null) {
    var isDisplay = match[1] !== undefined;
    var expr = isDisplay ? match[1] : match[2];

    try {
      katex.renderToString(expr, { throwOnError: true, displayMode: isDisplay });
    } catch (e) {
      var from = posFromIndex(content, match.index);
      var to   = posFromIndex(content, match.index + match[0].length);
      var msg  = e.message.replace(/^KaTeX parse error: /, '');
      latexMarks.push(editor.markText(from, to, {
        className: 'cm-latex-error',
        title: msg,
      }));
      errors.push({ line: from.line + 1, msg: msg });
    }
  }

  var panel = document.getElementById('latex-error-panel');
  var list  = document.getElementById('le-list');
  var title = document.getElementById('le-title');
  if (!panel || !list) return;

  if (errors.length === 0) {
    panel.style.display = 'none';
    list.innerHTML = '';
    return;
  }

  var count = errors.length;
  if (title) title.textContent = count + ' LaTeX error' + (count > 1 ? 's' : '');
  list.innerHTML = errors.map(function (e) {
    return '<div class="le-item">' +
      '<span class="le-line">L' + e.line + '</span>' +
      '<span class="le-msg">' + e.msg.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</span>' +
      '</div>';
  }).join('');
  panel.style.display = 'block';
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
