// ── Global keyboard shortcuts ─────────────────────────────────────────────────

document.addEventListener('keydown', function (ev) {
  var tag = document.activeElement && document.activeElement.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  if (document.activeElement && document.activeElement.closest('.CodeMirror')) return;
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;

  switch (ev.key) {
    case 'e':
      ev.preventDefault();
      if (typeof switchMode === 'function') switchMode('edit');
      break;
    case 's':
      ev.preventDefault();
      if (typeof switchMode === 'function') switchMode('slideshow');
      break;
    case 'p':
      ev.preventDefault();
      if (typeof switchMode === 'function') switchMode('pdf');
      break;
    case 'd':
      ev.preventDefault();
      if (typeof saveNote === 'function') saveNote();
      break;
    case 'l':
      if (typeof currentMode !== 'undefined' && currentMode === 'slideshow') {
        ev.preventDefault();
        if (typeof toggleLaser === 'function') toggleLaser();
      }
      break;
    case 'f':
      if (typeof currentMode !== 'undefined' && currentMode === 'slideshow') {
        ev.preventDefault();
        if (typeof toggleFullscreen === 'function') toggleFullscreen();
      }
      break;
  }
});
