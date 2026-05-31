"""
python manage.py seed

Creates demo data:
  - Superuser: admin@mdeck.dev / admin123
  - Demo user: demo@mdeck.dev
  - Category: Mathematics > Class 11
  - Published deck: Relations and Functions (16 slides, NCERT Ch 2)
  - Draft deck: Sample Deck (3 slides)
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from decks.models import Category, Deck, DeckVersion, Profile, Theme, generate_unique_slug


RELATIONS_AND_FUNCTIONS_MD = """\
## Relations and Functions
### Chapter 2 · Class 11 · NCERT Mathematics

*"Mathematics is the indispensable instrument of all physical research."*
— Berthelot

---

## Cartesian Product

Given two non-empty sets $A$ and $B$, the **Cartesian product** is:

$$A \\times B = \\{(a, b) : a \\in A,\\ b \\in B\\}$$

**Key properties:**
- If $n(A) = p$ and $n(B) = q$, then $n(A \\times B) = pq$
- $A \\times B \\neq B \\times A$ in general
- $A \\times \\phi = \\phi$
- $(a, b) = (c, d) \\Rightarrow a = c$ and $b = d$

---

## Cartesian Product — Example (NCERT Ex 3)

Let $A = \\{1,2,3\\}$, $B = \\{3,4\\}$, $C = \\{4,5,6\\}$

**Find** $A \\times (B \\cap C)$ and $(A \\times B) \\cap (A \\times C)$

$B \\cap C = \\{4\\}$

$$A \\times (B \\cap C) = \\{(1,4),\\ (2,4),\\ (3,4)\\}$$

$A \\times B = \\{(1,3),(1,4),(2,3),(2,4),(3,3),(3,4)\\}$

$A \\times C = \\{(1,4),(1,5),(1,6),(2,4),(2,5),(2,6),(3,4),(3,5),(3,6)\\}$

$$(A \\times B) \\cap (A \\times C) = \\{(1,4),\\ (2,4),\\ (3,4)\\}$$

Both results are equal — this is always true.

---

## Relations — Definition

A **relation** $R$ from set $A$ to set $B$ is a **subset** of $A \\times B$

$$R \\subseteq A \\times B$$

| Term | Meaning |
|------|---------|
| **Domain** | Set of all first elements (inputs) |
| **Range** | Set of all second elements (outputs) used |
| **Codomain** | The full set $B$ |

> **Note:** Range $\\subseteq$ Codomain

If $(a, b) \\in R$, we write $a\\ R\\ b$ — "$a$ is related to $b$"

---

## Relations — Example (NCERT Ex 7)

Let $A = \\{1,2,3,4,5,6\\}$, $R = \\{(x,y) : y = x+1\\}$

**All pairs in R:**

$$R = \\{(1,2),\\ (2,3),\\ (3,4),\\ (4,5),\\ (5,6)\\}$$

- **Domain** $= \\{1, 2, 3, 4, 5\\}$
- **Codomain** $= \\{1, 2, 3, 4, 5, 6\\}$
- **Range** $= \\{2, 3, 4, 5, 6\\}$

Note: $6 \\notin$ Domain because $y = 7 \\notin A$

---

## Number of Relations

The total number of relations from $A$ to $B$:

$$\\text{Number of relations} = 2^{pq}$$

where $n(A) = p$ and $n(B) = q$

**Why?** Each subset of $A \\times B$ is a valid relation, and a set with $pq$ elements has $2^{pq}$ subsets.

**Example:** $A = \\{1,2\\}$, $B = \\{3,4\\}$

$n(A \\times B) = 4$, so number of relations $= 2^4 = \\mathbf{16}$

---

## Functions — Definition

A **function** $f: A \\rightarrow B$ is a relation where every element of $A$ has **exactly one** image in $B$

$$f(a) = b \\Rightarrow b \\text{ is the image of } a,\\quad a \\text{ is the preimage of } b$$

**The rule:** one input $\\rightarrow$ exactly one output

**Requirements:**
- Every element of $A$ must be mapped
- No element of $A$ can have two different images
- Multiple elements of $A$ can map to the same element of $B$

---

## Function vs Not a Function (NCERT Ex 11)

Given $A = \\{1,2,3,4,5,6\\}$:

**R = {(2,1),(3,1),(4,2)} — Not a function**
Not every element of $A$ has an image

**R = {(2,2),(2,4),(3,3),(4,4)} — Not a function**
Element $2$ has two images: $2$ and $4$

**R = {(1,2),(2,3),(3,4),(4,5),(5,6),(6,7)} — Function**
Every element has exactly one image

---

## Special Functions (Part 1)

**Identity Function:** $f: \\mathbb{R} \\rightarrow \\mathbb{R}$, $f(x) = x$
- Domain: $\\mathbb{R}$, Range: $\\mathbb{R}$

**Constant Function:** $f: \\mathbb{R} \\rightarrow \\mathbb{R}$, $f(x) = c$
- Domain: $\\mathbb{R}$, Range: $\\{c\\}$

**Polynomial Function:**
$$f(x) = a_0 + a_1x + a_2x^2 + \\cdots + a_nx^n$$
where $a_i \\in \\mathbb{R}$ and $n$ is a non-negative integer

---

## Special Functions (Part 2)

**Modulus Function:**
$$f(x) = |x| = \\begin{cases} x & x \\geq 0 \\\\ -x & x < 0 \\end{cases}$$
Domain: $\\mathbb{R}$, Range: $[0, \\infty)$

**Signum Function:**
$$f(x) = \\begin{cases} 1 & \\text{if } x > 0 \\\\ 0 & \\text{if } x = 0 \\\\ -1 & \\text{if } x < 0 \\end{cases}$$
Domain: $\\mathbb{R}$, Range: $\\{-1, 0, 1\\}$

---

## Greatest Integer Function

$$f(x) = [x] = \\text{greatest integer} \\leq x$$

**Examples:**
- $[2.7] = 2$
- $[3.0] = 3$
- $[-1.3] = -2$
- $[-0.5] = -1$
- $[4] = 4$

Domain: $\\mathbb{R}$, Range: $\\mathbb{Z}$

Also called the **floor function**. The graph looks like a staircase.

---

## Example — Squaring Function (NCERT Ex 13)

$f(x) = x^2$, for $x \\in \\{-3, -2, -1, 0, 1, 2, 3\\}$

| $x$ | $-3$ | $-2$ | $-1$ | $0$ | $1$ | $2$ | $3$ |
|-----|------|------|------|-----|-----|-----|-----|
| $f(x)$ | $9$ | $4$ | $1$ | $0$ | $1$ | $4$ | $9$ |

- **Domain** $= \\{-3,-2,-1,0,1,2,3\\}$
- **Range** $= \\{0,1,4,9\\}$

For $f: \\mathbb{R} \\rightarrow \\mathbb{R}$, Domain $= \\mathbb{R}$, Range $= [0, \\infty)$

---

## Algebra of Functions

For functions $f, g: X \\rightarrow \\mathbb{R}$:

$$(f + g)(x) = f(x) + g(x)$$

$$(f - g)(x) = f(x) - g(x)$$

$$(fg)(x) = f(x) \\cdot g(x)$$

$$\\left(\\frac{f}{g}\\right)(x) = \\frac{f(x)}{g(x)}, \\quad g(x) \\neq 0$$

$$(\\alpha f)(x) = \\alpha \\cdot f(x), \\quad \\alpha \\in \\mathbb{R}$$

---

## Algebra of Functions — Example (NCERT Ex 16)

Given $f(x) = x^2$ and $g(x) = 2x + 1$

$$(f + g)(x) = x^2 + 2x + 1 = (x+1)^2$$

$$(f - g)(x) = x^2 - 2x - 1$$

$$(fg)(x) = x^2(2x+1) = 2x^3 + x^2$$

$$\\left(\\frac{f}{g}\\right)(x) = \\frac{x^2}{2x+1}, \\quad x \\neq -\\frac{1}{2}$$

---

## Common Mistakes

**Range vs Codomain:**
Range $\\subseteq$ Codomain, but Range $\\neq$ Codomain in general

**Cartesian Product:**
$A \\times B \\neq B \\times A$ (order of pairs matters)

**Relations vs Functions:**
Every function is a relation, but not every relation is a function

**Function Rule:**
One element in domain **cannot** map to two different images
(but two elements can map to the **same** image — that's allowed)

---

## Summary

| Concept | Definition |
|---------|-----------|
| Ordered pair | $(a,b)$: first element $a$, second $b$ |
| Cartesian product | $A \\times B = \\{(a,b): a \\in A, b \\in B\\}$ |
| Relation | Any subset $R \\subseteq A \\times B$ |
| Domain | $\\{a : (a,b) \\in R\\}$ |
| Range | $\\{b : (a,b) \\in R\\}$ |
| Codomain | The full set $B$ |
| Function | Relation where every $a \\in A$ has exactly one image |
| Algebra of $f,g$ | $(f \\pm g)$, $(fg)$, $(f/g)$ defined pointwise |"""


SAMPLE_DECK_MD = """\
## Welcome to mDeck
### markdown to slides, AI ready

Write **markdown**, present **slides**, export **PDF**.

---

## Slide Format

Separate slides with `---` on its own line.

Inline math: $E = mc^2$

Block math:

$$\\int_0^\\infty e^{-x}\\,dx = 1$$

---

## Code Blocks

```python
def hello():
    print("Hello from mDeck!")

hello()
```

- KaTeX math rendering
- Reveal.js presentations
- MCP AI integration"""


class Command(BaseCommand):
    help = 'Seed the database with demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # Fix site domain
        try:
            site = Site.objects.get(pk=1)
            site.domain = 'localhost:8000'
            site.name = 'mDeck'
            site.save()
        except Site.DoesNotExist:
            pass

        # ── Superuser ──────────────────────────────────────────────────────────
        admin, created = User.objects.get_or_create(
            email='admin@mdeck.dev',
            defaults={'username': 'admin', 'is_staff': True, 'is_superuser': True},
        )
        if created or not admin.has_usable_password():
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'  Created superuser: admin@mdeck.dev / admin123')
        else:
            self.stdout.write(f'  Superuser already exists: admin@mdeck.dev')

        Profile.objects.get_or_create(user=admin)

        # ── Demo user ──────────────────────────────────────────────────────────
        demo, created = User.objects.get_or_create(
            email='demo@mdeck.dev',
            defaults={'username': 'demo', 'first_name': 'Demo', 'last_name': 'Teacher'},
        )
        if created:
            demo.set_password('demo1234')
            demo.save()
            self.stdout.write(f'  Created demo user: demo@mdeck.dev / demo1234')
        else:
            self.stdout.write(f'  Demo user already exists: demo@mdeck.dev')

        demo_profile, _ = Profile.objects.get_or_create(user=demo)
        demo_profile.bio = 'High school mathematics teacher. Building slide decks for Class 11.'
        demo_profile.save()

        # ── Categories ─────────────────────────────────────────────────────────
        maths_cat, _ = Category.objects.get_or_create(
            user=demo,
            slug='mathematics',
            defaults={'name': 'Mathematics'},
        )
        class11_cat, _ = Category.objects.get_or_create(
            user=demo,
            slug='class-11',
            defaults={'name': 'Class 11', 'parent': maths_cat},
        )
        self.stdout.write('  Created categories: Mathematics > Class 11')

        # ── Published deck: Relations and Functions ────────────────────────────
        rf_slug = 'relations-and-functions'
        if Deck.objects.filter(slug=rf_slug).exists():
            rf_deck = Deck.objects.get(slug=rf_slug)
            self.stdout.write(f'  Published deck already exists: {rf_slug}')
        else:
            rf_deck = Deck.objects.create(
                owner=demo,
                title='Relations and Functions',
                slug=rf_slug,
                description='NCERT Class 11 Chapter 2. Covers Cartesian products, relations, functions, and algebra of functions. Full KaTeX equations with worked examples.',
                content=RELATIONS_AND_FUNCTIONS_MD,
                category=class11_cat,
                tags='mathematics,class-11,ncert,relations,functions',
                theme=Theme.objects.filter(slug='dark').first(),
                status='published',
                allow_copy=True,
                view_count=42,
            )
            DeckVersion.objects.create(deck=rf_deck, content=RELATIONS_AND_FUNCTIONS_MD)
            self.stdout.write(f'  Created published deck: Relations and Functions ({rf_deck.slide_count()} slides)')

        # ── Draft deck: Sample Deck ────────────────────────────────────────────
        sample_slug = 'sample-deck'
        if Deck.objects.filter(slug=sample_slug).exists():
            self.stdout.write(f'  Draft deck already exists: {sample_slug}')
        else:
            sample_deck = Deck.objects.create(
                owner=demo,
                title='Sample Deck',
                slug=sample_slug,
                description='A starter deck showing the slide format.',
                content=SAMPLE_DECK_MD,
                tags='sample,demo',
                theme=Theme.objects.filter(slug='dark').first(),
                status='draft',
            )
            DeckVersion.objects.create(deck=sample_deck, content=SAMPLE_DECK_MD)
            self.stdout.write(f'  Created draft deck: Sample Deck ({sample_deck.slide_count()} slides)')

        self.stdout.write(self.style.SUCCESS('\nDone! Seed data created.'))
        self.stdout.write('')
        self.stdout.write('  Admin:  admin@mdeck.dev / admin123')
        self.stdout.write('  Demo:   demo@mdeck.dev  / demo1234')
        self.stdout.write('  Run:    python manage.py runserver')
        self.stdout.write('  Open:   http://localhost:8000')
