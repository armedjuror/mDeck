import json

from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import APIKey, Category, Deck, DeckVersion, OAuthApp, Theme, generate_unique_slug

_FALLBACK_THEME = {'bg': '#0f0f0f', 'text': '#e0e0e0', 'accent': '#4ade80', 'code_bg': '#1a1a1a'}


def _resolve_theme(deck):
    """Return the deck's Theme instance, falling back to dark."""
    if deck.theme:
        return deck.theme
    return Theme.objects.filter(slug='dark').first()


# ── Index ─────────────────────────────────────────────────────────────────────

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


# ── Dashboard ──────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    decks = request.user.decks.all()

    status_filter = request.GET.get('status', '')
    category_slug = request.GET.get('category', '')
    q = request.GET.get('q', '')

    if status_filter:
        decks = decks.filter(status=status_filter)
    if category_slug:
        decks = decks.filter(category__slug=category_slug)

    categories = Category.objects.filter(user=request.user)

    return render(request, 'dashboard.html', {
        'decks': decks,
        'categories': categories,
        'current_status': status_filter,
        'current_category': category_slug,
        'q': q,
    })


# ── Deck detail (owner) ────────────────────────────────────────────────────────

@login_required
def deck_detail(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    Deck.objects.filter(pk=deck.pk).update(view_count=F('view_count') + 1)
    return render(request, 'deck_detail.html', {'deck': deck})


# ── Editor ────────────────────────────────────────────────────────────────────

@login_required
def deck_edit(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    categories = Category.objects.filter(user=request.user)
    themes = Theme.objects.all()
    return render(request, 'deck_edit.html', {
        'deck': deck,
        'categories': categories,
        'themes': themes,
        'font_choices': Deck.FONT_CHOICES,
    })


# ── Slideshow (owner) ─────────────────────────────────────────────────────────

@login_required
def deck_present(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    return render(request, 'deck_present.html', {
        'deck': deck,
        'theme': _resolve_theme(deck),
        'back_url': f'/deck/{slug}/',
    })


# ── Publish flow (owner) ──────────────────────────────────────────────────────

@login_required
@require_POST
def deck_submit_review(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    if deck.status == 'draft':
        deck.status = 'pending'
        deck.save(update_fields=['status'])
    return JsonResponse({'ok': True, 'status': deck.status})


@login_required
@require_POST
def deck_unpublish(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    deck.status = 'draft'
    deck.save(update_fields=['status'])
    return JsonResponse({'ok': True, 'status': deck.status})


@login_required
@require_POST
def deck_toggle_allow_copy(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    deck.allow_copy = not deck.allow_copy
    deck.save(update_fields=['allow_copy'])
    return JsonResponse({'ok': True, 'allow_copy': deck.allow_copy})


# ── Delete ────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def deck_delete(request, slug):
    deck = get_object_or_404(Deck, slug=slug, owner=request.user)
    deck.delete()
    return JsonResponse({'ok': True})


# ── Categories ────────────────────────────────────────────────────────────────

@login_required
def categories(request):
    cats = Category.objects.filter(user=request.user).select_related('parent')
    # Build tree: roots + children
    roots = [c for c in cats if c.parent_id is None]
    return render(request, 'categories.html', {
        'categories': cats,
        'roots': roots,
    })


@login_required
@require_POST
def category_create(request):
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    parent_id = data.get('parent_id')
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)
    from django.utils.text import slugify
    slug = slugify(name)
    if not slug:
        return JsonResponse({'error': 'Invalid name'}, status=400)
    # Ensure uniqueness for this user
    base_slug = slug
    counter = 1
    while Category.objects.filter(user=request.user, slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    parent = None
    if parent_id:
        parent = get_object_or_404(Category, id=parent_id, user=request.user)
    cat = Category.objects.create(user=request.user, name=name, slug=slug, parent=parent)
    return JsonResponse({
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'parent_id': cat.parent_id,
    })


@login_required
@require_POST
def category_delete(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id, user=request.user)
    cat.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def category_update(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id, user=request.user)
    data = json.loads(request.body)
    name = data.get('name', '').strip()
    if name:
        cat.name = name
        cat.save(update_fields=['name'])
    return JsonResponse({'ok': True, 'name': cat.name})


# ── Explore ────────────────────────────────────────────────────────────────────

def explore(request):
    decks = Deck.objects.filter(status='published').select_related('owner', 'category').order_by('-updated_at')

    q = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')

    if q:
        decks = decks.filter(Q(title__icontains=q) | Q(tags__icontains=q))
    if category_slug:
        decks = decks.filter(category__slug=category_slug)

    paginator = Paginator(decks, 24)
    page = paginator.get_page(request.GET.get('page', 1))

    # Categories that have at least one published deck
    pub_category_ids = Deck.objects.filter(status='published').exclude(
        category=None
    ).values_list('category_id', flat=True).distinct()
    pub_categories = Category.objects.filter(id__in=pub_category_ids).order_by('name')

    return render(request, 'explore.html', {
        'page': page,
        'q': q,
        'current_category': category_slug,
        'pub_categories': pub_categories,
    })


def explore_deck(request, slug):
    deck = get_object_or_404(Deck, slug=slug, status='published')
    Deck.objects.filter(pk=deck.pk).update(view_count=F('view_count') + 1)
    return render(request, 'deck_detail.html', {
        'deck': deck,
        'public_view': True,
    })


def explore_present(request, slug):
    deck = get_object_or_404(Deck, slug=slug, status='published')
    return render(request, 'deck_present.html', {
        'deck': deck,
        'theme': _resolve_theme(deck),
        'back_url': f'/explore/{slug}/',
    })


@login_required
@require_POST
def deck_copy(request, slug):
    deck = get_object_or_404(Deck, slug=slug, status='published', allow_copy=True)
    new_title = f'Copy of {deck.title}'
    new_slug = generate_unique_slug(new_title)
    owner_name = deck.owner.get_full_name() or deck.owner.email
    new_deck = Deck.objects.create(
        owner=request.user,
        title=new_title,
        slug=new_slug,
        content=deck.content,
        description=f'Copied from "{deck.title}" by {owner_name}.',
        theme=deck.theme,
        status='draft',
    )
    return JsonResponse({'ok': True, 'slug': new_deck.slug})


# ── Profile ────────────────────────────────────────────────────────────────────

@login_required
def profile(request):
    user_profile = request.user.profile
    api_keys = request.user.api_keys.all()
    oauth_apps = request.user.oauth_apps.all()
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'api_keys': api_keys,
        'oauth_apps': oauth_apps,
    })


@login_required
@require_POST
def profile_update(request):
    data = json.loads(request.body)
    user_profile = request.user.profile
    if 'bio' in data:
        user_profile.bio = data['bio']
    user_profile.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def api_key_generate(request):
    data = json.loads(request.body)
    name = data.get('name', 'My API Key').strip() or 'My API Key'
    api_key, raw_key = APIKey.generate(request.user, name)
    return JsonResponse({
        'ok': True,
        'id': api_key.id,
        'name': api_key.name,
        'prefix': api_key.prefix,
        'key': raw_key,  # shown once only
    })


@login_required
@require_POST
def api_key_revoke(request, key_id):
    api_key = get_object_or_404(APIKey, id=key_id, user=request.user)
    api_key.delete()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def oauth_app_create(request):
    data = json.loads(request.body)
    name = data.get('name', 'Claude Web').strip() or 'Claude Web'
    redirect_uris = data.get('redirect_uris', '').strip()
    app, raw_secret = OAuthApp.generate(request.user, name)
    if redirect_uris:
        app.redirect_uris = redirect_uris
        app.save(update_fields=['redirect_uris'])
    return JsonResponse({
        'ok': True,
        'id': app.id,
        'name': app.name,
        'client_id': app.client_id,
        'client_secret': raw_secret,
        'client_secret_prefix': app.client_secret_prefix,
    })


@login_required
@require_POST
def oauth_app_delete(request, app_id):
    app = get_object_or_404(OAuthApp, id=app_id, user=request.user)
    app.delete()
    return JsonResponse({'ok': True})
