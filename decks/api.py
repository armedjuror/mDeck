import base64
import datetime
import hashlib
import json
import secrets

from django.contrib.auth.views import redirect_to_login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

from .models import APIKey, Category, Deck, DeckVersion, OAuthApp, OAuthCode, OAuthToken, Theme, generate_unique_slug


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


# ── CORS helper (MCP & OAuth endpoints are called cross-origin by Claude) ─────

_CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Authorization, Content-Type',
    'Access-Control-Max-Age': '86400',
}

def _cors(response):
    for k, v in _CORS_HEADERS.items():
        response[k] = v
    return response

def _cors_preflight():
    r = HttpResponse('', status=204)
    for k, v in _CORS_HEADERS.items():
        r[k] = v
    return r


# ── MCP endpoint (Bearer token auth, no CSRF) ─────────────────────────────────

def _mcp_auth(request):
    """Extract and validate Bearer token. Returns User or None."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    raw_key = auth[7:].strip()

    # Check API key first
    user = APIKey.validate(raw_key)
    if user:
        return user

    # Check OAuth token
    token_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    try:
        token = OAuthToken.objects.select_related('user').get(token_hash=token_hash)
        token.last_used = timezone.now()
        token.save(update_fields=['last_used'])
        return token.user
    except OAuthToken.DoesNotExist:
        return None


@csrf_exempt
def mcp_endpoint(request):
    if request.method == 'OPTIONS':
        return _cors_preflight()

    if request.method == 'GET':
        # Server does not offer SSE — per MCP spec return 405
        return _cors(HttpResponse('', status=405))

    if request.method != 'POST':
        return _cors(JsonResponse({'error': 'Method not allowed'}, status=405))

    user = _mcp_auth(request)
    if not user:
        base = _base_url(request)
        response = JsonResponse({
            'jsonrpc': '2.0',
            'id': None,
            'error': {'code': -32001, 'message': 'Unauthorized'},
        }, status=401)
        response['WWW-Authenticate'] = (
            f'Bearer realm="mDeck",'
            f' resource_metadata="{base}/.well-known/oauth-protected-resource"'
        )
        return _cors(response)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _cors(JsonResponse({
            'jsonrpc': '2.0',
            'id': None,
            'error': {'code': -32700, 'message': 'Parse error'},
        }, status=400))

    rpc_id = body.get('id')
    method = body.get('method', '')
    params = body.get('params') or {}

    # Notifications have no id — acknowledge with 202 per MCP spec
    if rpc_id is None and method.startswith('notifications/'):
        return _cors(HttpResponse('', status=202))

    try:
        result = _dispatch_mcp(user, method, params)
    except ValueError as e:
        return _cors(JsonResponse({
            'jsonrpc': '2.0',
            'id': rpc_id,
            'error': {'code': -32601, 'message': str(e)},
        }, status=200))
    except Exception:
        return _cors(JsonResponse({
            'jsonrpc': '2.0',
            'id': rpc_id,
            'error': {'code': -32603, 'message': 'Internal error'},
        }, status=200))

    return _cors(JsonResponse({'jsonrpc': '2.0', 'id': rpc_id, 'result': result}))


def _dispatch_mcp(user, method, params):
    # ── MCP protocol methods ──────────────────────────────────────────────────
    if method == 'initialize':
        # Negotiate protocol version — prefer what the client requests if we support it
        _supported = ['2025-03-26', '2024-11-05']
        requested = params.get('protocolVersion', '2024-11-05')
        negotiated = requested if requested in _supported else _supported[0]
        return {
            'protocolVersion': negotiated,
            'capabilities': {'tools': {}},
            'serverInfo': {'name': 'mDeck', 'version': '1.0.0'},
            'instructions': (
                "mDeck is a markdown slide deck tool. Each deck is a markdown document "
                "where slides are separated by a line containing only --- (with blank lines around it).\n\n"
                "SLIDE STRUCTURE:\n"
                "## Slide Title\n"
                "### Optional subtitle\n\n"
                "Content here. Keep each slide focused on one idea.\n\n"
                "---\n\n"
                "## Next Slide\n\n"
                "- Bullet point\n"
                "- **Bold**, *italic*, `inline code`\n\n"
                "MATH (KaTeX):\n"
                "- Inline: $E = mc^2$\n"
                "- Block: $$\\int_0^\\infty e^{-x}\\,dx = 1$$\n\n"
                "CODE BLOCKS:\n"
                "```python\n"
                "def hello():\n"
                "    print('Hello')\n"
                "```\n\n"
                "TOOLS:\n"
                "- create_deck: new deck with title + full markdown content\n"
                "- update_deck: replace a deck's content (use slug)\n"
                "- append_slide: add one slide to end (markdown only, no ---)\n"
                "- get_deck: read full content and metadata\n"
                "- list_decks: see all decks\n\n"
                "TIPS: Use ## for every slide title. 5-7 bullet points max per slide. "
                "One concept per slide. Math-heavy slides work best with $$...$$ blocks on their own line."
            ),
        }
    elif method == 'tools/list':
        return {'tools': _mcp_tools_schema()}
    elif method == 'tools/call':
        return _mcp_call_tool(user, params.get('name', ''), params.get('arguments') or {})
    # ── Legacy direct methods (API key clients) ───────────────────────────────
    elif method == 'list_decks':
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


def _mcp_tools_schema():
    return [
        {
            'name': 'list_decks',
            'description': 'List all your decks',
            'inputSchema': {'type': 'object', 'properties': {}},
        },
        {
            'name': 'get_deck',
            'description': 'Get a deck by slug, including full markdown content',
            'inputSchema': {
                'type': 'object',
                'properties': {'slug': {'type': 'string', 'description': 'Deck slug'}},
                'required': ['slug'],
            },
        },
        {
            'name': 'create_deck',
            'description': 'Create a new deck',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'title': {'type': 'string'},
                    'content': {'type': 'string', 'description': 'Markdown content, slides separated by \\n---\\n'},
                    'theme': {'type': 'string', 'enum': ['dark', 'chalk', 'sepia', 'ocean', 'paper', 'forest']},
                    'tags': {'type': 'string', 'description': 'Comma-separated tags'},
                    'category': {'type': 'string', 'description': 'Category name'},
                },
                'required': ['title'],
            },
        },
        {
            'name': 'update_deck',
            'description': 'Update an existing deck',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'slug': {'type': 'string'},
                    'content': {'type': 'string'},
                    'title': {'type': 'string'},
                    'tags': {'type': 'string'},
                    'theme': {'type': 'string'},
                },
                'required': ['slug'],
            },
        },
        {
            'name': 'append_slide',
            'description': 'Append a new slide to an existing deck',
            'inputSchema': {
                'type': 'object',
                'properties': {
                    'slug': {'type': 'string'},
                    'slide_content': {'type': 'string', 'description': 'Markdown for the new slide (without ---)'},
                },
                'required': ['slug', 'slide_content'],
            },
        },
        {
            'name': 'list_categories',
            'description': 'List all your categories as a nested tree',
            'inputSchema': {'type': 'object', 'properties': {}},
        },
    ]


def _mcp_call_tool(user, name, args):
    handlers = {
        'list_decks': lambda: _mcp_list_decks(user),
        'get_deck': lambda: _mcp_get_deck(user, args),
        'create_deck': lambda: _mcp_create_deck(user, args),
        'update_deck': lambda: _mcp_update_deck(user, args),
        'append_slide': lambda: _mcp_append_slide(user, args),
        'list_categories': lambda: _mcp_list_categories(user),
    }
    if name not in handlers:
        raise ValueError(f'Unknown tool: {name}')
    result = handlers[name]()
    return {'content': [{'type': 'text', 'text': json.dumps(result, indent=2, default=str)}]}


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
    host = _base_url(request)
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


# ── OAuth 2.0 (for Claude.ai web and other OAuth clients) ─────────────────────

@csrf_exempt
def oauth_register(request):
    """OAuth 2.0 Dynamic Client Registration (RFC 7591).
    Claude and other MCP clients call this to self-register before the auth flow."""
    if request.method == 'OPTIONS':
        return _cors_preflight()
    if request.method != 'POST':
        return _cors(JsonResponse({'error': 'method_not_allowed'}, status=405))

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'invalid_client_metadata'}, status=400)

    client_name = (body.get('client_name') or 'MCP Client')[:100]
    redirect_uris_raw = body.get('redirect_uris', [])
    if not isinstance(redirect_uris_raw, list) or not redirect_uris_raw:
        return JsonResponse({
            'error': 'invalid_client_metadata',
            'error_description': 'redirect_uris is required',
        }, status=400)

    # DCR apps are owned by the first superuser (admin) since no user is
    # logged in at registration time. Authorization is still scoped to
    # the individual user who approves the OAuth flow.
    from django.contrib.auth import get_user_model
    User = get_user_model()
    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not owner:
        return JsonResponse({'error': 'server_error'}, status=500)

    app, raw_secret = OAuthApp.generate(owner, client_name)
    app.redirect_uris = '\n'.join(str(u) for u in redirect_uris_raw)
    app.save(update_fields=['redirect_uris'])

    return _cors(JsonResponse({
        'client_id': app.client_id,
        'client_secret': raw_secret,
        'client_name': client_name,
        'redirect_uris': redirect_uris_raw,
        'grant_types': ['authorization_code'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'client_secret_post',
    }, status=201))

def _base_url(request):
    """Build the base URL with the correct scheme.
    Cloudflare terminates TLS and forwards over HTTP, so request.scheme is
    always 'http' on the origin. CF-Visitor contains the real client scheme."""
    host = request.build_absolute_uri('/').rstrip('/')
    cf_visitor = request.META.get('HTTP_CF_VISITOR', '')
    x_forwarded = request.META.get('HTTP_X_FORWARDED_PROTO', '')
    if '"scheme":"https"' in cf_visitor or x_forwarded == 'https':
        host = 'https://' + host.split('://', 1)[-1]
    return host


def oauth_protected_resource(request):
    """RFC 9728 — lets MCP clients discover the authorization server for this resource."""
    if request.method == 'OPTIONS':
        return _cors_preflight()
    base = _base_url(request)
    return _cors(JsonResponse({
        'resource': f'{base}/api/mcp/',
        'authorization_servers': [base],
        'bearer_methods_supported': ['header'],
        'resource_documentation': f'{base}/profile/',
    }))


def oauth_metadata(request):
    if request.method == 'OPTIONS':
        return _cors_preflight()
    host = _base_url(request)
    return _cors(JsonResponse({
        'issuer': host,
        'authorization_endpoint': f'{host}/oauth/authorize/',
        'token_endpoint': f'{host}/oauth/token/',
        'registration_endpoint': f'{host}/oauth/register/',
        'response_types_supported': ['code'],
        'grant_types_supported': ['authorization_code'],
        'token_endpoint_auth_methods_supported': ['client_secret_post', 'none'],
        'scopes_supported': ['mcp'],
        'code_challenge_methods_supported': ['S256'],
    }))


def oauth_authorize(request):
    client_id = request.GET.get('client_id') or request.POST.get('client_id', '')
    redirect_uri = request.GET.get('redirect_uri') or request.POST.get('redirect_uri', '')
    state = request.GET.get('state') or request.POST.get('state', '')
    response_type = request.GET.get('response_type', 'code')
    code_challenge = request.GET.get('code_challenge') or request.POST.get('code_challenge', '')
    code_challenge_method = request.GET.get('code_challenge_method') or request.POST.get('code_challenge_method', '')

    try:
        app = OAuthApp.objects.select_related('user').get(client_id=client_id)
    except OAuthApp.DoesNotExist:
        return HttpResponse('Unknown client_id', status=400, content_type='text/plain')

    allowed = app.get_redirect_uris()
    if allowed and redirect_uri not in allowed:
        return HttpResponse('redirect_uri not allowed', status=400, content_type='text/plain')

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())

    if request.method == 'POST':
        action = request.POST.get('action', '')
        sep = '&' if '?' in redirect_uri else '?'

        if action == 'approve':
            code_str = secrets.token_urlsafe(32)
            OAuthCode.objects.create(
                app=app,
                user=request.user,
                code=code_str,
                redirect_uri=redirect_uri,
                expires_at=timezone.now() + datetime.timedelta(minutes=5),
                code_challenge=request.POST.get('code_challenge', ''),
                code_challenge_method=request.POST.get('code_challenge_method', ''),
            )
            url = f'{redirect_uri}{sep}code={code_str}'
            if state:
                url += f'&state={state}'
            return HttpResponseRedirect(url)

        # deny
        url = f'{redirect_uri}{sep}error=access_denied'
        if state:
            url += f'&state={state}'
        return HttpResponseRedirect(url)

    return render(request, 'oauth_authorize.html', {
        'app': app,
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': code_challenge_method,
    })


def _verify_pkce(code_verifier, code_challenge, method):
    """Returns True if code_verifier satisfies the stored code_challenge."""
    if method == 'S256':
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        computed = base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')
        return computed == code_challenge
    # plain (not recommended but allowed)
    if method == 'plain':
        return code_verifier == code_challenge
    return False


@csrf_exempt
def oauth_token(request):
    if request.method == 'OPTIONS':
        return _cors_preflight()
    if request.method != 'POST':
        return _cors(JsonResponse({'error': 'method_not_allowed'}, status=405))

    content_type = request.content_type or ''
    if 'application/json' in content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'invalid_request'}, status=400)
        client_id = body.get('client_id', '')
        client_secret = body.get('client_secret', '')
        code = body.get('code', '')
        redirect_uri = body.get('redirect_uri', '')
        code_verifier = body.get('code_verifier', '')
    else:
        client_id = request.POST.get('client_id', '')
        client_secret = request.POST.get('client_secret', '')
        code = request.POST.get('code', '')
        redirect_uri = request.POST.get('redirect_uri', '')
        code_verifier = request.POST.get('code_verifier', '')

    try:
        app = OAuthApp.objects.get(client_id=client_id)
    except OAuthApp.DoesNotExist:
        return JsonResponse({'error': 'invalid_client'}, status=401)

    # Allow public clients (no client_secret) when PKCE is used
    if client_secret and not app.verify_secret(client_secret):
        return JsonResponse({'error': 'invalid_client'}, status=401)

    try:
        auth_code = OAuthCode.objects.select_related('user').get(code=code, app=app, used=False)
    except OAuthCode.DoesNotExist:
        return JsonResponse({'error': 'invalid_grant'}, status=400)

    if auth_code.expires_at < timezone.now():
        return JsonResponse({'error': 'invalid_grant', 'error_description': 'Code expired'}, status=400)

    if auth_code.redirect_uri != redirect_uri:
        return JsonResponse({'error': 'invalid_grant'}, status=400)

    # Validate PKCE if the authorization request included a code_challenge
    if auth_code.code_challenge:
        if not code_verifier:
            return JsonResponse({'error': 'invalid_grant', 'error_description': 'code_verifier required'}, status=400)
        if not _verify_pkce(code_verifier, auth_code.code_challenge, auth_code.code_challenge_method):
            return JsonResponse({'error': 'invalid_grant', 'error_description': 'PKCE verification failed'}, status=400)

    auth_code.used = True
    auth_code.save(update_fields=['used'])

    raw_token = 'mdeck_' + secrets.token_urlsafe(32)
    OAuthToken.objects.create(
        app=app,
        user=auth_code.user,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
    )

    return _cors(JsonResponse({
        'access_token': raw_token,
        'token_type': 'Bearer',
        'scope': 'mcp',
        'expires_in': 31536000,  # 1 year; no server-side expiry enforced yet
    }))
