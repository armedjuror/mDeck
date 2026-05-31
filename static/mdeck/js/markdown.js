// ── Marked + KaTeX setup (call once via setupMarked()) ───────────────────────

var markedReady = false;

function setupMarked() {
  if (markedReady) return;
  markedReady = true;

  var renderer = new marked.Renderer();

  // Mac-style code window with line numbers and syntax highlighting
  renderer.code = function (token) {
    var code = typeof token === 'object' ? (token.text || '') : token;
    var lang = typeof token === 'object' ? (token.lang || '') : (arguments[1] || '');

    var hi;
    try {
      hi = lang && hljs.getLanguage(lang)
        ? hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
        : hljs.highlightAuto(code).value;
    } catch (e) {
      hi = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }

    var lines = hi.split('\n');
    if (lines[lines.length - 1] === '') lines.pop();

    var body = lines.map(function (l, i) {
      return '<span class="cw-line"><span class="cw-ln">' + (i + 1) +
        '</span><span class="cw-lc">' + l + '</span></span>';
    }).join('');

    return '<div class="code-window"><div class="cw-bar">' +
      '<span class="cw-dot" style="background:#ff5f57"></span>' +
      '<span class="cw-dot" style="background:#febc2e"></span>' +
      '<span class="cw-dot" style="background:#28c840"></span>' +
      (lang ? '<span class="cw-lang">' + lang + '</span>' : '') +
      '</div><pre class="cw-pre"><code>' + body + '</code></pre></div>';
  };

  marked.use({ renderer: renderer });
  marked.use(markedKatex({
    throwOnError: false,
    output: 'html',
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$',  right: '$',  display: false },
    ],
  }));
  marked.setOptions({ gfm: true, breaks: false });
}

function renderMd(md) {
  return marked.parse(md);
}

function splitSlides(md) {
  return md.split(/\n---\n/).map(function (s) { return s.trim(); }).filter(Boolean);
}
