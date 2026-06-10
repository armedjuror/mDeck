# mDeck

Markdown-to-slides for technical content. mDeck produces editable text — not images — so formulas, code, and structure stay exact and AI-editable.

Other tools generate a picture per slide. When a formula is wrong, you regenerate the image. In mDeck every formula is a string: fix it with a text edit, or tell an AI to fix it, and move on.

**Live:** [mdeck.dev](https://mdeck.dev)

---

## Why this exists

My mother teaches higher-secondary mathematics with a textbook and a board. Making decks for her chapters took about 40 minutes each in PowerPoint, and image-based AI tools couldn't be trusted to render LaTeX reliably.

The solution: connect Claude to mDeck, give it a chapter PDF, get back a markdown deck. Every theorem is a text string. Every correction is a text edit. Human and AI share the same file.

---

## Features

| | |
|---|---|
| **Markdown editor** | CodeMirror 5, Dracula theme, live split-pane preview |
| **Reveal.js slideshows** | Fade transitions, keyboard nav, fullscreen, laser pointer |
| **KaTeX math** | Inline `$E=mc^2$` and block `$$\int...$$` on every slide |
| **PDF export** | One-click download via html2pdf.js |
| **6 themes · 7 fonts** | dark · chalk · sepia · ocean · paper · forest |
| **Public gallery** | Publish decks, allow community copies |
| **MCP server** | Connect Claude or any MCP client — full tool access |
| **Categories** | Nested category tree for deck organisation |
---

## Quickstart

### Use the hosted version

Sign up at [mdeck.dev](https://mdeck.dev) — free, no credit card.

### Self-host

**1. Clone and install**

```bash
git clone https://github.com/armedjuror/mDeck.git
cd mDeck
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment**

```bash
cp .env.example .env
```

Minimum `.env` for local development:

```env
SECRET_KEY=any-long-random-string
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

**3. Migrate and seed demo data**

```bash
python manage.py migrate
python manage.py seed
```

**4. Run**

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000)

**Demo accounts after seeding:**

| Role | Email | Password |
|---|---|---|
| Admin | `admin@mdeck.dev` | `admin123` |
| Teacher | `demo@mdeck.dev` | `demo1234` |

---

## MCP Setup

mDeck exposes an MCP server at `/api/mcp/`. Connect Claude or any MCP client to create and manage decks directly.

### Claude Code

```bash
claude mcp add mdeck \
  --transport http \
  --url https://mdeck.dev/api/mcp/ \
  --header "Authorization: Bearer YOUR_API_KEY"
```

Generate an API key at **Profile → API Keys → Generate**.

### Claude.ai (web)

1. Go to **Settings → Connectors → Add**
2. Enter your server URL: `https://mdeck.dev/api/mcp/`
3. Claude auto-registers and opens the sign-in flow — no credentials needed

### MCP tools

| Tool | What it does |
|---|---|
| `list_decks` | List all your decks with metadata |
| `get_deck` | Get full markdown content of a deck |
| `create_deck` | Create a deck with title, content, theme, tags |
| `update_deck` | Update title, content, theme, or tags |
| `append_slide` | Append a new slide to an existing deck |
| `list_categories` | List your category tree |

---

## Slide format

Slides are separated by `---` on its own line with blank lines around it:

```markdown
## Slide Title
### Subtitle

Content here. Inline math: $E = mc^2$

---

## Equations

Block math:

$$
\int_0^\infty e^{-x}\,dx = 1
$$

---

## Code

```python
def hello():
    print("Hello, world!")
```

---

## Tables and quotes

> "Direct quote."
> — Author

| Column A | Column B |
|---|---|
| value | value |
```

Math uses KaTeX syntax. All standard markdown (bold, italic, lists, links, images) works on every slide.

---

## Environment variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key — long random string |
| `DATABASE_URL` | PostgreSQL or SQLite connection string |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain.com` |
| `RESEND_API_KEY` | Resend API key for transactional email |
| `DEFAULT_FROM_EMAIL` | Sender name and address |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (optional) |

Without `RESEND_API_KEY`, emails print to the console (fine for local dev).

---

## Google OAuth setup

1. [Google Cloud Console](https://console.cloud.google.com/) → **APIs & Services → Credentials → OAuth 2.0 Client ID** (Web application)
2. Add `http://localhost:8000/auth/google/login/callback/` to **Authorized redirect URIs**
3. Add to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
4. Django admin → **Sites** → change `example.com` → `localhost:8000`
5. **Social Applications → Add → Google** → paste credentials → assign to site

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x, Python 3.12 |
| Database | PostgreSQL (production) / SQLite (local) |
| Auth | django-allauth — email + Google OAuth |
| Frontend | Vanilla JS, no build step |
| Editor | CodeMirror 5 (Dracula theme) |
| Slideshow | Reveal.js 5 (embedded mode) |
| Math | KaTeX 0.16 + marked-katex-extension |
| Markdown | Marked.js 12 |
| PDF | html2pdf.js |
| Static files | WhiteNoise |
| Deployment | Gunicorn + Cloudflare |

---

## Project structure

```
mdeck/                  Django project (settings, urls, wsgi)
decks/                  Main app
  models.py             Deck, Category, Theme, APIKey, OAuthApp, OAuthToken
  views.py              All page views
  api.py                MCP endpoint, OAuth 2.0 server, JSON-RPC dispatch
  admin.py              Deck approval workflow
  email_backend.py      Resend email backend
  management/
    commands/seed.py    Demo data seeder
templates/              Django HTML templates
static/mdeck/
  css/base.css          Design system, nav, cards, responsive
  css/editor.css        Editor/slideshow layout
  js/app.js             Shared utilities
  js/editor.js          CodeMirror, split preview, save
  js/slideshow.js       Reveal.js, fullscreen, laser pointer
  js/pdf.js             PDF export
```

---

## Deployment notes

- The `Procfile` `release` command runs `python manage.py migrate` automatically on deploy
- Static files served via **WhiteNoise** — no separate static server needed
- Works behind Cloudflare — `CF-Visitor` header used for correct HTTPS URL generation

---

## Approving decks for the public gallery

1. User submits a deck → status becomes `pending`
2. Django admin → **Decks** → select → Action: **Approve selected decks**
3. Status becomes `published` → deck appears in the Explore gallery

---

## Contributing

Contributions are welcome. mDeck is a small project — bug fixes, docs, and well-scoped features all help.

### Ways to contribute

- **Bug reports** — open an issue with steps to reproduce and expected behaviour
- **Feature requests** — open an issue with the `enhancement` label; describe the use case
- **Code** — fork, make changes, open a pull request
- **Decks** — share well-formatted example decks via the public gallery

### Development setup

```bash
git clone https://github.com/armedjuror/mDeck.git
cd mDeck
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edit with your settings
python manage.py migrate
python manage.py seed
python manage.py runserver
```

### Pull request guidelines

1. **One concern per PR** — keep changes focused; don't mix bug fixes with refactors
2. **No build step** — frontend is vanilla JS + CDN; do not introduce npm or any bundler
3. **Keep the design system** — use existing CSS variables (`--bg`, `--accent`, `--surface`, etc.); no new CSS frameworks
4. **No rounded corners above 2px** — design rule
5. **Test locally** — run the dev server and verify before opening a PR
6. **Describe your PR** — explain what changed and why; screenshots help for UI changes

### Reporting security issues

Do not open a public issue for security vulnerabilities.
Email: **armedjuror [at] gmail [dot] com**

---

## License

MIT
