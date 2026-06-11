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
      '</div><pre class="cw-pre"><code class="hljs">' + body + '</code></pre></div>';
  };

  marked.use({ renderer: renderer });
  marked.use(markedKatex({
    throwOnError: false,
    errorColor: '#ff6b6b',
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

// ── Per-slide frontmatter ─────────────────────────────────────────────────────
// Whitelist of recognized config keys. Anything else means the block is content.
var _FM_WHITELIST = { bg: true, reveal: true };

/**
 * Parse optional frontmatter at the top of a raw slide string.
 * Returns { config: {bg?, reveal?}, content: string }.
 * If the first line is not a whitelisted key: value, the entire text is content.
 */
function parseSlideFrontmatter(text) {
  var lines = text.split('\n');
  var firstMatch = lines.length && lines[0].match(/^(\w+)\s*:\s*(.+)$/);
  if (!firstMatch || !_FM_WHITELIST[firstMatch[1]]) {
    return { config: {}, content: text };
  }
  var config = {};
  var i = 0;
  while (i < lines.length) {
    if (lines[i] === '') break;
    var m = lines[i].match(/^(\w+)\s*:\s*(.+)$/);
    if (!m || !_FM_WHITELIST[m[1]]) break;
    config[m[1]] = m[2].trim();
    i++;
  }
  // Skip one blank line after the config block
  if (i < lines.length && lines[i] === '') i++;
  return { config: config, content: lines.slice(i).join('\n') };
}

/**
 * Split markdown into plain content strings (frontmatter stripped).
 * Used by preview and PDF — no config needed there.
 */
function splitSlides(md) {
  return md.split(/\n---\n/).map(function (s) {
    var parsed = parseSlideFrontmatter(s.trim());
    return parsed.content.trim();
  }).filter(Boolean);
}

/**
 * Split markdown into [{config, content}] objects.
 * Used by the slideshow renderer.
 */
function splitSlidesWithConfig(md) {
  return md.split(/\n---\n/).map(function (s) {
    var parsed = parseSlideFrontmatter(s.trim());
    return { config: parsed.config, content: parsed.content.trim() };
  }).filter(function (s) { return s.content; });
}
