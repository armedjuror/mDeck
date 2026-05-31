import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import APIKey, Category, Deck, DeckVersion, Theme, generate_unique_slug


# ── Internal API (CSRF protected, session auth) ───────────────────────────────

@login_required
@require_POST
def deck_new(request):
    data = json.loads(request.body)
    title = data.get('title', 'Untitled Deck').strip() or 'Untitled Deck'
    slug = generate_unique_slug(title)
    deck = Deck.objects.create(
        owner=request.user,
        title=title,
        slug=slug,
        content='## ' + title + '\n\n---\n\n## Slide 2\n\nYour content here.',
    )
    return JsonResponse({'ok': True, 'slug': deck.slug})


@login_required
@require_POST
def deck_save(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    data = json.loads(request.body)

    if 'content' in data:
        deck.content = data['content']
    if 'title' in data and data['title'].strip():
        deck.title = data['title'].strip()
    if 'theme' in data:
        t = Theme.objects.filter(slug=data['theme']).first()
        if t:
            deck.theme = t
    if 'font' in data and data['font'] in dict(Deck.FONT_CHOICES):
        deck.font = data['font']
    if 'font_size' in data:
        try:
            deck.font_size = max(10, min(120, int(data['font_size'])))
        except (ValueError, TypeError):
            pass
    if 'description' in data:
        deck.description = data['description']
    if 'tags' in data:
        deck.tags = data['tags']
    if 'category_id' in data:
        if data['category_id']:
            cat = get_object_or_404(Category, id=data['category_id'], user=request.user)
            deck.category = cat
        else:
            deck.category = None

    deck.save()

    # Create a version snapshot
    DeckVersion.objects.create(deck=deck, content=deck.content)

    return JsonResponse({
        'ok': True,
        'updated_at': deck.updated_at.isoformat(),
        'title': deck.title,
        'slug': deck.slug,
    })


@login_required
@require_POST
def deck_autosave(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    data = json.loads(request.body)
    content = data.get('content', '')
    # Only create a version; don't update the deck itself
    DeckVersion.objects.create(deck=deck, content=content)
    return JsonResponse({'ok': True})


# ── MCP endpoint (Bearer token auth, no CSRF) ─────────────────────────────────

def _mcp_auth(request):
    """Extract and validate Bearer token. Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    raw_key = auth[7:].strip()
    return APIKey.validate(raw_key)


@csrf_exempt
def mcp_endpoint(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    user = _mcp_auth(request)
    if not user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    method = body.get('method', '')
    params = body.get('params', {})

    try:
        result = _dispatch_mcp(user, method, params)
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'Internal error'}, status=500)

    return JsonResponse({'result': result})


def _dispatch_mcp(user, method, params):
    if method == 'list_decks':
        return _mcp_list_decks(user)
    elif method == 'get_deck':
        return _mcp_get_deck(user, params)
    elif method == 'create_deck':
        return _mcp_create_deck(user, params)
    elif method == 'update_deck':
        return _mcp_update_deck(user, params)
    elif method == 'append_slide':
        return _mcp_append_slide(user, params)
    elif method == 'list_categories':
        return _mcp_list_categories(user)
    else:
        raise ValueError(f'Unknown method: {method}')


def _mcp_list_decks(user):
    decks = Deck.objects.filter(owner=user).select_related('theme')
    return [
        {
            'id': d.id,
            'title': d.title,
            'slug': d.slug,
            'status': d.status,
            'updated_at': d.updated_at.isoformat(),
            'theme': d.theme.slug if d.theme else 'dark',
            'tags': d.tags,
        }
        for d in decks
    ]


def _mcp_get_deck(user, params):
    slug = params.get('slug', '')
    if not slug:
        raise ValueError('slug is required')
    deck = get_object_or_404(Deck, slug=slug, owner=user)
    return {
        'title': deck.title,
        'slug': deck.slug,
        'content': deck.content,
        'theme': deck.theme.slug if deck.theme else 'dark',
        'category': deck.category.name if deck.category else None,
        'tags': deck.tags,
        'status': deck.status,
        'slide_count': deck.slide_count(),
        'updated_at': deck.updated_at.isoformat(),
    }


def _mcp_create_deck(user, params):
    title = params.get('title', 'Untitled Deck').strip() or 'Untitled Deck'
    content = params.get('content', f'## {title}\n\nYour content here.')
    theme_slug = params.get('theme', 'dark')
    tags = params.get('tags', '')
    slug = generate_unique_slug(title)

    category = None
    cat_name = params.get('category')
    if cat_name:
        category = Category.objects.filter(user=user, name__iexact=cat_name).first()

    theme = Theme.objects.filter(slug=theme_slug).first() or Theme.objects.filter(slug='dark').first()

    deck = Deck.objects.create(
        owner=user,
        title=title,
        slug=slug,
        content=content,
        theme=theme,
        tags=tags,
        category=category,
    )
    DeckVersion.objects.create(deck=deck, content=content)
    return {
        'slug': deck.slug,
        'edit_url': f'/deck/{deck.slug}/edit/',
        'present_url': f'/deck/{deck.slug}/present/',
    }


def _mcp_update_deck(user, params):
    slug = params.get('slug', '')
    if not slug:
        raise ValueError('slug is required')
    deck = get_object_or_404(Deck, slug=slug, owner=user)

    if 'content' in params:
        deck.content = params['content']
    if 'title' in params and params['title'].strip():
        deck.title = params['title'].strip()
    if 'tags' in params:
        deck.tags = params['tags']
    if 'theme' in params:
        t = Theme.objects.filter(slug=params['theme']).first()
        if t:
            deck.theme = t
    deck.save()
    DeckVersion.objects.create(deck=deck, content=deck.content)
    return {'updated_at': deck.updated_at.isoformat(), 'slug': deck.slug}


def _mcp_append_slide(user, params):
    slug = params.get('slug', '')
    slide_content = params.get('slide_content', '')
    if not slug:
        raise ValueError('slug is required')
    if not slide_content.strip():
        raise ValueError('slide_content is required')
    deck = get_object_or_404(Deck, slug=slug, owner=user)
    deck.content = deck.content.rstrip() + '\n\n---\n\n' + slide_content.strip()
    deck.save()
    DeckVersion.objects.create(deck=deck, content=deck.content)
    return {'updated_at': deck.updated_at.isoformat(), 'slide_count': deck.slide_count()}


def _mcp_list_categories(user):
    cats = Category.objects.filter(user=user).select_related('parent')

    def cat_to_dict(c):
        return {
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'parent': c.parent.name if c.parent else None,
            'deck_count': c.deck_count(),
        }

    roots = [c for c in cats if c.parent_id is None]
    result = []
    for root in roots:
        item = cat_to_dict(root)
        item['children'] = [cat_to_dict(c) for c in cats if c.parent_id == root.id]
        result.append(item)
    return result


@require_GET
def mcp_manifest(request):
    host = request.build_absolute_uri('/').rstrip('/')
    manifest = {
        'schema_version': 'v1',
        'name': 'mDeck',
        'description': 'Create and manage markdown slide decks. markdown to slides, AI ready.',
        'contact_email': '',
        'auth': {
            'type': 'api_key',
            'instructions': 'Generate an API key from your mDeck profile page (/profile/). Pass it as: Authorization: Bearer <key>',
        },
        'api': {
            'type': 'json-rpc',
            'url': f'{host}/api/mcp/',
        },
        'tools': [
            {
                'name': 'list_decks',
                'description': 'List all your decks',
                'parameters': {},
            },
            {
                'name': 'get_deck',
                'description': 'Get a deck by slug, including full markdown content',
                'parameters': {
                    'slug': {'type': 'string', 'required': True, 'description': 'Deck slug'},
                },
            },
            {
                'name': 'create_deck',
                'description': 'Create a new deck',
                'parameters': {
                    'title': {'type': 'string', 'required': True},
                    'content': {'type': 'string', 'required': False, 'description': 'Markdown content, slides separated by \\n---\\n'},
                    'theme': {'type': 'string', 'required': False, 'enum': ['dark', 'chalk', 'sepia', 'ocean', 'paper', 'forest']},
                    'tags': {'type': 'string', 'required': False, 'description': 'Comma-separated tags'},
                    'category': {'type': 'string', 'required': False, 'description': 'Category name'},
                },
            },
            {
                'name': 'update_deck',
                'description': 'Update an existing deck',
                'parameters': {
                    'slug': {'type': 'string', 'required': True},
                    'content': {'type': 'string', 'required': False},
                    'title': {'type': 'string', 'required': False},
                    'tags': {'type': 'string', 'required': False},
                    'theme': {'type': 'string', 'required': False},
                },
            },
            {
                'name': 'append_slide',
                'description': 'Append a new slide to an existing deck',
                'parameters': {
                    'slug': {'type': 'string', 'required': True},
                    'slide_content': {'type': 'string', 'required': True, 'description': 'Markdown for the new slide (without ---)'},
                },
            },
            {
                'name': 'list_categories',
                'description': 'List all your categories as a nested tree',
                'parameters': {},
            },
        ],
    }
    return JsonResponse(manifest)
