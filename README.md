# slidenotes

A static GitHub Pages site for creating and presenting markdown-based slideshows.

## Quick start (local)

```sh
python3 -m http.server
# open http://localhost:8000
```

## Adding a new note

1. Create a `.md` file in `notes/` (e.g. `notes/my-topic.md`)
2. Add an entry to `notes/index.json`:

```json
{
  "file": "my-topic.md",
  "title": "My Topic",
  "subject": "Subject",
  "class": "Class 12",
  "updated": "2026-05-31"
}
```

## Slide separator

Separate slides with `---` on its own line:

```md
## Slide 1

Content here.

---

## Slide 2

More content.
```

## Math syntax

- Inline: `$E = mc^2$`
- Block: `$$\int_0^\infty e^{-x}\,dx = 1$$`

## Saving

The **Save & Download** button in Edit mode downloads the `.md` file to your computer. Replace the file in `notes/` and push to update the live site.

## GitHub Pages setup

In repo Settings → Pages → Source: **Deploy from branch** `main`, folder `/root`.
