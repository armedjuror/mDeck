// ── PDF rendering ─────────────────────────────────────────────────────────────

function renderPdf() {
  if (typeof setupMarked === 'function') setupMarked();
  var slides = splitSlides(currentMarkdown);
  var container = document.getElementById('pdf-render');
  if (!container) return;
  container.innerHTML = slides.map(function (s) {
    return '<div class="slide-block">' + renderMd(s) + '</div>';
  }).join('');
}

window.downloadPdf = function () {
  renderPdf();
  var btn = document.getElementById('btn-download-pdf');
  if (btn) { btn.disabled = true; btn.textContent = 'Generating...'; }

  var filename = (typeof DECK_SLUG !== 'undefined' ? DECK_SLUG : 'deck') + '.pdf';

  html2pdf().set({
    margin: [12, 12, 12, 12],
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
  }).from(document.getElementById('pdf-render')).save()
    .then(function () {
      if (btn) { btn.disabled = false; btn.textContent = '\u2193 Download PDF'; }
      showToast('PDF downloaded');
    })
    .catch(function () {
      if (btn) { btn.disabled = false; btn.textContent = '\u2193 Download PDF'; }
      showToast('PDF generation failed');
    });
};
