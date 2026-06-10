# mDeck

**Markdown to slides, AI ready.**

mDeck is an open-source web application for teachers and educators to write markdown notes, present them as interactive slideshows, and export to PDF — with a built-in MCP server so AI assistants like Claude can create and manage decks directly.

🌐 **Live:** [mdeck.armedjuror.in](https://mdeck.armedjuror.in)

---

## Features

| | |
|---|---|
| ✍️ **Markdown editor** | CodeMirror 5 with Dracula theme, live split-pane preview |
| 🎞️ **Reveal.js presentations** | Fade transitions, keyboard nav, fullscreen, laser pointer |
| 📐 **KaTeX math** | Inline `$E=mc^2$` and block `$$\int...$$` on every slide |
| 🖨️ **PDF export** | One-click download via html2pdf.js |
| 🎨 **6 slide themes** | dark · chalk · sepia · ocean · paper · forest |
| 🔤 **7 UI fonts** | JetBrains Mono · Inter · Merriweather · Lora · DM Sans · Fraunces · Outfit |
| 🌍 **Public gallery** | Publish decks, allow community copies |
| 🔐 **Google OAuth** | Sign in with Google |
| 🤖 **MCP server** | Full OAuth 2.0 + Dynamic Client Registration — connect Claude and any MCP client |
| 📂 **Categories** | Nested category tree for deck organization |

---

## Quick Start (Local)

### 1. Clone and install

```bash
git clone https://github.com/your-username/mdeck.git
cd mdeck
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Minimum `.env` for local development (SQLite, no Google auth):

```env
SECRET_KEY=any-long-random-string-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Migrate and seed demo data

```bash
python manage.py migrate
python manage.py seed
```

### 4. Run

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

## Slide Format

Slides are separated by `---` on its own line (with blank lines around it):

```markdown
## Slide Title
### Subtitle

Content here. Inline math: $E = mc^2$

---

## Code Slide

```python
def hello():
    print("Hello, world!")
```

---

## Math Slide

Block equation:

$$
\int_0^\infty e^{-x}\,dx = 1
$$

- Bullet point
- **Bold**, *italic*, `code`

---

## Quote & Table

> "Direct quote from source."
> — Author

| Feature | Status |
|---|---|
| KaTeX | ✓ |
| PDF export | ✓ |
```

---

## MCP Integration

mDeck exposes a fully spec-compliant MCP server at `/api/mcp/` supporting:

- **OAuth 2.0** with Dynamic Client Registration (RFC 7591)
- **PKCE** (S256) — no client secret needed for public clients
- **JSON-RPC 2.0** transport (Streamable HTTP)
- Protocol versions `2025-03-26` and `2024-11-05`

### Connect Claude.ai (web)

1. Go to **Claude.ai → Settings → Connectors → Add**
2. Enter your server URL: `https://your-domain.com/api/mcp/`
3. Claude auto-registers via DCR and opens the sign-in flow — no credentials needed

### Connect Claude Code (CLI)

```bash
claude mcp add mdeck \
  --transport http \
  --url https://your-domain.com/api/mcp/ \
  --header "Authorization: Bearer YOUR_API_KEY"
```

Or add manually to `~/.claude.json`:

```json
{
  "mcpServers": {
    "mdeck": {
      "type": "http",
      "url": "https://your-domain.com/api/mcp/",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

Generate an API key at **Profile → API Keys → Generate**.

### MCP Tools

| Tool | Description |
|---|---|
| `list_decks` | List all your decks with metadata |
| `get_deck` | Get full markdown content of a deck by slug |
| `create_deck` | Create a new deck with title, content, theme, tags |
| `update_deck` | Update title, content, theme, or tags of a deck |
| `append_slide` | Append a new slide to an existing deck |
| `list_categories` | List your category tree |

### OAuth Endpoints

| Endpoint | URL |
|---|---|
| Metadata discovery | `/.well-known/oauth-authorization-server` |
| Authorization | `/oauth/authorize/` |
| Token exchange | `/oauth/token/` |
| Dynamic registration | `/oauth/register/` |

---

## Google OAuth Setup

1. [Google Cloud Console](https://console.cloud.google.com/) → Create project → APIs & Services → Credentials → **OAuth 2.0 Client ID** (Web application)
2. Add `http://localhost:8000/accounts/google/login/callback/` to **Authorized redirect URIs**
3. Add to `.env`:
   ```env
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
4. Django admin → **Sites** → change `example.com` → `localhost:8000`
5. **Social Applications** → Add → Google → paste credentials → assign to site

---

## Deployment

### Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key (long random string) |
| `DATABASE_URL` | PostgreSQL connection string |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Comma-separated hostnames |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain.com` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (optional) |

### Notes

- The `Procfile` `release` command runs `python manage.py migrate` automatically on deploy
- Static files are served via **WhiteNoise** — no separate static server needed
- The app works behind Cloudflare — `CF-Visitor` header is used for correct HTTPS URL generation

---

## Project Structure

```
mdeck/                  Django project (settings, urls, wsgi)
decks/                  Main app
  models.py             Deck, Category, Theme, APIKey, OAuthApp, OAuthToken
  views.py              All page views
  api.py                MCP endpoint, OAuth 2.0 server, JSON-RPC dispatch
  admin.py              Deck approval workflow
  management/
    commands/seed.py    Demo data seeder
templates/              Django HTML templates (9 pages)
static/mdeck/
  css/base.css          Design system, nav, cards, footer, responsive
  css/editor.css        Editor/slideshow full-screen layout
  js/app.js             showToast, formatDate, switchMode
  js/markdown.js        Marked.js + KaTeX setup (guarded by markedReady)
  js/editor.js          CodeMirror, split preview, save, draft persistence
  js/slideshow.js       Reveal.js, fullscreen, laser pointer
  js/pdf.js             html2pdf export
  js/shortcuts.js       Global keyboard shortcuts
```

---

## Approving Decks for the Public Gallery

1. User submits a deck for review → status becomes `pending`
2. Django admin → **Decks** → select → Action: **Approve selected decks**
3. Status becomes `published` → deck appears in the public Explore gallery

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.x, Python 3.12 |
| Database | PostgreSQL (Supabase in production) / SQLite (local) |
| Auth | django-allauth (email + Google OAuth) |
| Frontend | Vanilla JS, no build step |
| Editor | CodeMirror 5 (Dracula theme) |
| Slideshow | Reveal.js 5 (embedded mode) |
| Math | KaTeX 0.16 + marked-katex-extension |
| Markdown | Marked.js 12 |
| PDF | html2pdf.js |
| Static files | WhiteNoise |
| Deployment | Gunicorn + Cloudflare |

---

## License

MIT
