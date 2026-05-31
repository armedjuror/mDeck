# mDeck

**markdown to slides, AI ready**

mDeck is a multi-user Django web app for creating and presenting markdown-based slideshows. Write markdown in a CodeMirror editor with live preview, present with Reveal.js, export to PDF, and let AI assistants build decks via the MCP API.

---

## Features

- **Markdown editor** — CodeMirror 5 with dracula theme, live side-by-side preview
- **KaTeX math** — inline `$E=mc^2$` and block `$$\int ...$$`
- **Reveal.js presentations** — fade transitions, keyboard nav, fullscreen, laser pointer
- **PDF export** — one-click download via html2pdf.js
- **6 slide themes** — dark, chalk, sepia, ocean, paper, forest (per deck)
- **7 UI fonts** — JetBrains Mono, Inter, Merriweather, Lora, DM Sans, Fraunces, Outfit
- **Google OAuth** — sign in with Google
- **Public gallery** — publish decks, allow copies
- **MCP server** — AI assistants can create/update decks via API key

---

## Local Setup

### 1. Clone and create virtualenv

```bash
git clone <repo>
cd mdeck
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create `.env`

```bash
cp .env.example .env
```

Minimum `.env` for local dev (SQLite, no Google auth):

```
SECRET_KEY=any-long-random-string
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### 3. Migrate and seed

```bash
python manage.py migrate
python manage.py seed
```

### 4. Run

```bash
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000)

Demo accounts after seeding:
- Admin: `admin@mdeck.dev` / `admin123`
- Demo teacher: `demo@mdeck.dev` / `demo1234`

---

## Slide Format

Slides are separated by `---` on its own line:

```markdown
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

```python
def hello():
    print("Hello!")
```
```

### Math

- Inline: `$formula$`
- Block: `$$formula$$`

### Themes

Set per deck in the editor header. Options: `dark`, `chalk`, `sepia`, `ocean`, `paper`, `forest`.

### Fonts

Set in your profile. Options: JetBrains Mono, Inter, Merriweather, Lora, DM Sans, Fraunces, Outfit.

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → APIs & Services → Credentials → OAuth 2.0 Client ID (Web application)
3. Add `http://localhost:8000/auth/google/login/callback/` to Authorized redirect URIs
4. Copy Client ID and Secret to `.env`
5. In Django admin: Sites → change `example.com` to `localhost:8000`
6. Social Applications → Add → Google → paste Client ID and Secret → assign to site

---

## MCP Setup (Claude Desktop)

mDeck exposes a JSON-RPC MCP server at `/api/mcp/`.

### 1. Generate an API key

Sign in → Profile → API Keys → Generate

### 2. Add to Claude Desktop config

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mdeck": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"],
      "env": {
        "API_URL": "http://localhost:8000/api/mcp/",
        "API_KEY": "mdeck_your_key_here"
      }
    }
  }
}
```

Manifest URL for auto-discovery: `http://localhost:8000/api/mcp/manifest.json`

### MCP tools

| Tool | Description |
|---|---|
| `list_decks` | List all your decks |
| `get_deck` | Get deck content by slug |
| `create_deck` | Create a new deck |
| `update_deck` | Update title/content/theme/tags |
| `append_slide` | Append a slide to an existing deck |
| `list_categories` | List your category tree |

---

## Deploy to Railway / Render

Set environment variables:
- `SECRET_KEY` — long random string
- `DATABASE_URL` — PostgreSQL connection string
- `DEBUG` — `False`
- `ALLOWED_HOSTS` — your deploy domain
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`

The `Procfile` `release` command runs `python manage.py migrate` automatically on deploy.

---

## Project Structure

```
mdeck/              Django project settings
decks/              Main app (models, views, api, admin)
templates/          Django templates
static/mdeck/
  css/base.css      Global styles, design system
  css/editor.css    Editor/slideshow layout
  js/app.js         showToast, formatDate, switchMode
  js/markdown.js    setupMarked (KaTeX + code windows)
  js/editor.js      CodeMirror, preview, save, autosave
  js/slideshow.js   Reveal.js, fullscreen, laser
  js/pdf.js         html2pdf export
  js/shortcuts.js   Keyboard shortcuts
```

---

## Admin: Approving Decks

1. User submits deck for review (status → `pending`)
2. Django admin → Decks → select deck → Action: **Approve selected decks**
3. Status becomes `published` — deck appears in public gallery
