# slidenotes — Full Implementation Reference

A static GitHub Pages site for a teacher to write markdown notes, view them as slideshows, and download PDFs.
Dark, minimal, monospaced aesthetic. No build step. No frameworks. Everything via CDN.
Served over HTTP — use `python3 -m http.server`, then open `http://localhost:8000`.

---

## Repo Structure

```
/
├── index.html              ← notes listing page
├── note.html               ← editor + slideshow + PDF page
├── assets/
│   ├── style.css           ← all styles for both pages
│   └── app.js              ← shared utilities (showToast, formatDate)
├── notes/
│   ├── index.json          ← manually maintained note registry
│   ├── relations-functions.md
│   └── note_2.md
└── CLAUDE.md
```

---

## Design System

Defined as CSS variables in `:root` in `style.css`:

```css
--bg: #0f0f0f
--surface: #1a1a1a
--border: #2a2a2a
--text: #e0e0e0
--muted: #666
--accent: #4ade80   /* green */
--font: 'JetBrains Mono', monospace
```

Rules: no rounded corners (2px max), no gradients, no shadows. Max content width `860px` centered.

---

## CDN Dependencies (all loaded in `note.html` `<head>`)

| Library | Version | Purpose |
|---|---|---|
| KaTeX | 0.16.10 | Math rendering |
| marked-katex-extension | 5.0.0 | KaTeX inside Marked |
| Marked.js | 12.0.0 | Markdown → HTML |
| CodeMirror 5 | 5.65.16 | Markdown editor (dracula theme) |
| Reveal.js | 5.1.0 | Slideshow (black theme) |
| highlight.js | 11.9.0 | Code syntax highlighting (atom-one-dark theme) |
| html2pdf.js | 0.10.1 | PDF export |

**Critical**: KaTeX scripts must NOT have `defer` attribute. `markedKatex` calls `katex.renderToString` synchronously at setup time — if KaTeX loads after `marked-katex-extension`, you get `renderToString is not a function`.

---

## `notes/index.json`

Manually maintained. Each entry:

```json
{
  "file": "my-note.md",
  "title": "My Note Title",
  "subject": "Mathematics",
  "class": "Class 11",
  "updated": "2026-05-31"
}
```

---

## `assets/app.js` — Shared Utilities

```js
showToast(msg, duration = 2200)   // shows #toast div with .show class for duration ms
formatDate(dateStr)               // "2026-05-31" → "May 31, 2026"
```

Loaded by both `index.html` and `note.html` via `<script src="assets/app.js">`.

---

## `index.html` — Notes Listing Page

### Layout
Header (logo + New Note button) → search bar → notes grid → footer.

### Behaviour
- On load: `fetch('notes/index.json')` → render note cards
- Search input filters cards live by `title` and `subject` (case-insensitive substring)
- Clicking a card navigates to `note.html?file=filename.md`
- On `index.json` fetch failure, show friendly error
- On page load, checks `localStorage.getItem('slidenotes_draft')`. If a draft exists, changes the "+ New Note" button to "Resume draft →" and adds `.has-draft` class for different styling

---

## `note.html` — Editor + Slideshow + PDF

### URL Parameters
- `?file=filename.md` — load an existing note from `notes/`
- `?new=1` — new note mode (blank editor, draft saved to localStorage)

### Three Modes

Toggled via tab bar at top: **Edit**, **Slideshow** (default on load), **PDF**.

`switchMode(mode)` handles transitions:
- Adds `.active` to selected tab, shows `#mode-{mode}`, hides others via `.hidden`
- On switch to **edit**: calls `ensureEditor()`, then after 30ms refreshes CodeMirror and auto-opens preview if not already open
- On switch to **slideshow**: calls `renderSlideshow()`; also turns off laser if active
- On switch to **pdf**: calls `renderPdf()`

---

## Mode 1: Edit

### HTML Structure

```
#mode-edit (flex column)
  #edit-content-area (flex row)
    #editor-pane
      #editor-body
        textarea#editor-textarea   ← CodeMirror replaces this on init
    #split-divider                 ← hidden unless preview open
    #split-preview-pane            ← hidden unless preview open
      .split-pane-header           ← "Preview  live" label
      #split-preview               ← slide preview cards rendered here
  .editor-footer                   ← full width, below both panes
    .btn-preview-toggle            ← "⊞ Preview" / "⊟ Preview"
    #filename-wrap (new note only) ← filename input + Discard button
    .btn-save                      ← "Save & Download d"
```

### CodeMirror (`ensureEditor`)

Initialized **once** — guarded by `editorReady` boolean. Calling twice is a no-op.

```js
editor = CodeMirror.fromTextArea(textarea, {
  mode: 'markdown', theme: 'dracula',
  lineNumbers: true, lineWrapping: true,
  extraKeys: {
    'Ctrl-S'/'Cmd-S': saveNote,
    'Esc': () => switchMode('slideshow')   // exits editor back to slideshow
  }
});
editor.setValue(currentMarkdown);
```

**CSS trick for CodeMirror in flex containers**: must use `position: absolute; inset: 0` on `.CodeMirror`. Setting `height: 100%` alone doesn't work when the parent is a flex child without an explicit height.

### Live Preview

`togglePreview()` shows/hides the preview pane. Default: **open** (auto-called when entering Edit mode).

When opening preview:
- Removes `.hidden` from `#split-divider` and `#split-preview-pane`
- Sets `#editor-pane` flex: `style.flex = '0 0 50%'` (uses `splitPct` variable)
- Calls `renderPreview()` immediately

Preview re-renders 400ms after each editor change (debounced via `previewTimer`).

### Preview Rendering — Scale-Down Approach

Each slide is rendered at the real **960×700px** canvas size, then scaled down to fit the preview pane width using `transform: scale()`. This gives a pixel-perfect match with the actual slideshow.

HTML structure for each slide card:
```html
<div class="sp-wrap">
  <div class="sp-num">Slide N / M</div>
  <div class="sp-outer">              <!-- width:100%; aspect-ratio:960/700; overflow:hidden; position:relative -->
    <div class="sp-scale-wrap">       <!-- position:absolute; width:960px; height:700px; transform-origin:top left -->
      <div class="sp-slide">          <!-- width:960px; height:700px; font-size:40px; padding:56px 77px -->
        <!-- rendered HTML -->
      </div>
    </div>
  </div>
</div>
```

`scalePreviewSlides()` reads each `.sp-outer`'s current width and applies:
```js
wrap.style.transform = 'scale(' + (outer.offsetWidth / 960) + ')';
```

Called after: `renderPreview()`, window resize, divider drag.

### Draggable Divider

`mousedown` on `#split-divider` → sets `dragging = true`.
`mousemove` on `document` (while dragging):
```js
splitPct = clamp(20, 80, (e.clientX - modeEditRect.left) / modeEditRect.width * 100);
editorPane.style.flex = '0 0 ' + splitPct + '%';
```

**Critical**: must use `style.flex = '0 0 N%'`, NOT `style.width`. The pane has CSS `flex: 1` which sets `flex-basis: 0`. Setting `flex-basis` via the `flex` shorthand overrides it; `style.width` is ignored.

### Slide-Aware Scroll Sync

Both directions use `scrollTo({ behavior: 'smooth' })`. A `scrollLock` flag (released after 300ms) prevents feedback loops.

**`getSlideLineRanges()`**: splits editor content on `---` lines → returns `[{start, end}]` line number ranges, one per slide.

**Editor → Preview**:
1. `editor.lineAtHeight(scrollInfo.top, 'local')` → current top visible line
2. Find which slide range contains that line
3. `preview.scrollTo({ top: wrap.getBoundingClientRect().top - preview.getBoundingClientRect().top + preview.scrollTop, behavior: 'smooth' })`

**Preview → Editor**:
1. Find `.sp-wrap` whose top is closest to the preview container's top (via `getBoundingClientRect`)
2. Get that slide's first line from `getSlideLineRanges()`
3. `editor.getScrollerElement().scrollTo({ top: coords.top, behavior: 'smooth' })`

### Save & Download

`saveNote()` creates a `Blob` → `URL.createObjectURL` → programmatically clicks `<a download>`.

For new notes: also clears `localStorage['slidenotes_draft']` and shows a toast instructing user to add the file to `notes/` and update `index.json`.

### New Note Draft Persistence

When `?new=1`:
- Loads existing draft from `localStorage['slidenotes_draft']` on boot
- Auto-saves to localStorage 600ms after each editor change (debounced via `draftTimer`)
- Clears localStorage on save or discard
- `discardDraft()` confirms with user, removes draft, redirects to `index.html`

---

## Mode 2: Slideshow

### Reveal.js Config

Initialized **once** — guarded by `revealReady` boolean. On subsequent visits to the tab: `revealInst.sync()` + `layout()` + `slide(0)`.

```js
new Reveal(document.querySelector('#mode-slideshow .reveal'), {
  hash: false, transition: 'fade', backgroundTransition: 'fade',
  center: true, controls: true, progress: true,
  slideNumber: 'c/t', keyboard: true, overview: true,
  embedded: true,   // fills container, not full viewport
  margin: 0.08,
  width: 960, height: 700
})
```

**Do NOT use Reveal's built-in markdown plugin** — CORS issues with local file fetches. Instead: parse MD → HTML with Marked+KaTeX first, split on `\n---\n`, wrap each chunk in `<section>`, inject into `#reveal-slides`.

**Embedded mode** requires the `.reveal-container` to be `position: absolute; inset: 0` so Reveal fills it correctly.

After any layout change (fullscreen toggle, window resize), call `revealInst.layout()`.

### Reveal.js Font Size

Controlled in `style.css`:
```css
.reveal { font-size: 40px !important; }
```
All heading/paragraph sizes (`h2: 1.6em`, `p: 0.85em`, etc.) are relative to this. Change this value to scale all slide content.

Similarly for preview:
```css
.sp-slide { font-size: 40px; }
```
Keep both equal for preview to match slideshow exactly.

### Slideshow Controls (bottom-left overlay)

`#slideshow-controls` is `position: absolute; bottom: 48px; left: 12px; z-index: 2000`.

**Fullscreen** (`f` key or button):
- `document.fullscreenElement` check → `exitFullscreen()` or `el.requestFullscreen()`
- `fullscreenchange` listener updates button text and calls `revealInst.layout()` after 50ms

**Laser pointer** (`l` key or button):
- Toggles `#laser-dot` visibility (a `position: fixed` red glowing circle, `pointer-events: none`)
- `mousemove` on `document` sets `dot.style.left/top = e.clientX/Y + 'px'`
- Hides the cursor on the slideshow element while active (`cursor: none`)
- Automatically turned off when switching away from slideshow

---

## Mode 3: PDF

Renders all slides as stacked `.slide-block` divs (continuous, not Reveal) in `#pdf-render`, then:

```js
html2pdf().set({
  margin: [12, 12, 12, 12],
  filename: 'notename.pdf',
  image: { type: 'jpeg', quality: 0.98 },
  html2canvas: { scale: 2, useCORS: true },
  jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
}).from(pdfRenderEl).save()
```

PDF is generated from the vertical render, not from Reveal — gives cleaner output.

---

## Keyboard Shortcuts

Global `keydown` listener. Skipped when focus is in `INPUT`, `TEXTAREA`, or `.CodeMirror`, or when `Ctrl/Meta/Alt` is held:

| Key | Action |
|---|---|
| `e` | Switch to Edit mode |
| `s` | Switch to Slideshow mode |
| `p` | Switch to PDF mode |
| `d` | Save & Download |
| `f` | Toggle fullscreen (slideshow only) |
| `l` | Toggle laser pointer (slideshow only) |
| `Esc` | (in CodeMirror) Switch back to slideshow |
| `Ctrl/Cmd-S` | (in CodeMirror) Save & Download |

---

## Markdown Rendering Pipeline

### `setupMarked()` — guarded by `markedReady` flag

```js
marked.use({ renderer })          // custom code block renderer
marked.use(markedKatex({ ... }))  // KaTeX math with $...$ and $$...$$
marked.setOptions({ gfm: true, breaks: false })
```

**Must only call `marked.use()` once** — calling it multiple times stacks extensions and breaks rendering silently. Guard with `markedReady` boolean.

### Code Block Renderer

Fenced code blocks render as mac-style editor windows with:
- Title bar: red/yellow/green dots + language label
- Line numbers (`cw-ln`) + syntax-highlighted code (`cw-lc`) per line
- Syntax highlighting via `hljs.highlight(code, { language })` or `hljs.highlightAuto(code)`

```html
<div class="code-window">
  <div class="cw-bar">
    <span class="cw-dot" style="background:#ff5f57"></span>
    <span class="cw-dot" style="background:#febc2e"></span>
    <span class="cw-dot" style="background:#28c840"></span>
    <span class="cw-lang">python</span>
  </div>
  <pre class="cw-pre"><code>
    <span class="cw-line"><span class="cw-ln">1</span><span class="cw-lc">...</span></span>
  </code></pre>
</div>
```

### Math Syntax
- Inline: `$E = mc^2$`
- Block: `$$\int_0^\infty e^{-x}\,dx = 1$$`

### Slide Splitting
```js
md.split(/\n---\n/).map(s => s.trim()).filter(Boolean)
```

---

## CSS Layout Architecture

### `note.html` full-height layout

```
body
  .note-header          52px, border-bottom
  #main-area            height: calc(100vh - 52px); overflow: hidden; display: flex
    #mode-edit | #mode-slideshow | #mode-pdf    (only one visible at a time via .hidden)
```

### Edit mode flex hierarchy

```
#mode-edit              flex: 1; flex-direction: column; overflow: hidden
  #edit-content-area    flex: 1; min-height: 0; flex-direction: row; overflow: hidden
    #editor-pane        flex: 1 (or '0 0 N%' when preview open); min-width: 0
      #editor-body      flex: 1; position: relative; overflow: hidden
        .CodeMirror     position: absolute; inset: 0   ← fills parent
    #split-divider      flex: 0 0 5px; cursor: col-resize
    #split-preview-pane flex: 1; min-width: 0; overflow: hidden
      #split-preview    flex: 1; overflow-y: auto; padding: 20px 24px
  .editor-footer        flex-shrink: 0; full width
```

`min-height: 0` on `#edit-content-area` is critical — without it, flex children can't shrink below their content height and the editor overflows the viewport.

### Slideshow container

```
#mode-slideshow         flex: 1; position: relative; overflow: hidden
  .reveal-container     position: absolute; inset: 0
    .reveal             fills container (Reveal embedded mode)
```

---

## Known Pitfalls & Solutions

| Problem | Cause | Solution |
|---|---|---|
| `renderToString is not a function` | KaTeX loaded with `defer` | Remove `defer` from KaTeX script tags |
| Slideshow empty after tab switch | `marked.use()` called multiple times, stacking extensions | Guard with `markedReady` boolean |
| Reveal.js shows 0×0 | Initialized while container is `display:none` | Use `position:absolute; inset:0` on container + call `revealInst.layout()` after init |
| Draggable divider does nothing | Setting `style.width` on a `flex:1` item (flex-basis:0 overrides width) | Use `style.flex = '0 0 N%'` instead |
| CodeMirror doesn't fill its container | `height: 100%` fails in flex without explicit parent height | Use `position: absolute; inset: 0` on `.CodeMirror` |
| Scroll sync causes jitter loops | Each programmatic scroll triggers the other listener | Set `scrollLock = true`, release after 300ms |
| Preview doesn't match slideshow | Approximating Reveal CSS with cqi units is imprecise | Render preview at real 960×700, scale down with `transform: scale()` |

---

## Adding a New Note

1. Create `notes/my-note.md`
2. Add entry to `notes/index.json`
3. Serve over HTTP: `python3 -m http.server`

## Markdown Note Format

Slides separated by `---` on its own line (with blank lines around it):

```md
## Slide Title
### Subtitle

Content here. Inline math: $E = mc^2$

---

## Slide 2

Block math:

$$\int_0^\infty e^{-x}\,dx = 1$$

- Bullet point
- **Bold**, *italic*

---

## Slide 3

\`\`\`python
def hello():
    print("Hello")
\`\`\`
```

---

## GitHub Pages Setup

Repo Settings → Pages → Source: **Deploy from branch** `main`, folder `/root`.
No workflow file needed — GitHub Pages serves static files directly.
