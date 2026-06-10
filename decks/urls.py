from django.urls import path

from . import api, views

urlpatterns = [
    # ── Public / auth ──────────────────────────────────────────────────────────
    path('', views.index, name='index'),

    # ── Dashboard ──────────────────────────────────────────────────────────────
    path('dashboard/', views.dashboard, name='dashboard'),

    # ── Deck management ────────────────────────────────────────────────────────
    path('deck/<slug:slug>/', views.deck_detail, name='deck_detail'),
    path('deck/<slug:slug>/edit/', views.deck_edit, name='deck_edit'),
    path('deck/<slug:slug>/present/', views.deck_present, name='deck_present'),
    path('deck/<slug:slug>/submit/', views.deck_submit_review, name='deck_submit_review'),
    path('deck/<slug:slug>/unpublish/', views.deck_unpublish, name='deck_unpublish'),
    path('deck/<slug:slug>/allow-copy/', views.deck_toggle_allow_copy, name='deck_toggle_allow_copy'),
    path('deck/<slug:slug>/delete/', views.deck_delete, name='deck_delete'),

    # ── Categories ────────────────────────────────────────────────────────────
    path('categories/', views.categories, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:cat_id>/delete/', views.category_delete, name='category_delete'),
    path('categories/<int:cat_id>/update/', views.category_update, name='category_update'),

    # ── Explore ───────────────────────────────────────────────────────────────
    path('explore/', views.explore, name='explore'),
    path('explore/<slug:slug>/', views.explore_deck, name='explore_deck'),
    path('explore/<slug:slug>/present/', views.explore_present, name='explore_present'),
    path('explore/<slug:slug>/copy/', views.deck_copy, name='deck_copy'),

    # ── Profile ───────────────────────────────────────────────────────────────
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('profile/api-keys/generate/', views.api_key_generate, name='api_key_generate'),
    path('profile/api-keys/<int:key_id>/revoke/', views.api_key_revoke, name='api_key_revoke'),
    path('profile/oauth-apps/create/', views.oauth_app_create, name='oauth_app_create'),
    path('profile/oauth-apps/<int:app_id>/delete/', views.oauth_app_delete, name='oauth_app_delete'),

    # ── OAuth 2.0 ─────────────────────────────────────────────────────────────
    path('.well-known/oauth-authorization-server', api.oauth_metadata, name='oauth_metadata'),
    path('oauth/authorize/', api.oauth_authorize, name='oauth_authorize'),
    path('oauth/token/', api.oauth_token, name='oauth_token'),
    path('oauth/register/', api.oauth_register, name='oauth_register'),
    # Fallback paths per MCP spec (used when metadata discovery fails)
    path('authorize', api.oauth_authorize, name='oauth_authorize_fallback'),
    path('token', api.oauth_token, name='oauth_token_fallback'),
    path('register', api.oauth_register, name='oauth_register_fallback'),

    # ── API ───────────────────────────────────────────────────────────────────
    path('api/deck/new/', api.deck_new, name='api_deck_new'),
    path('api/deck/<slug:slug>/save/', api.deck_save, name='api_deck_save'),
    path('api/deck/<slug:slug>/autosave/', api.deck_autosave, name='api_deck_autosave'),
    path('api/mcp/manifest.json', api.mcp_manifest, name='mcp_manifest'),
    path('api/mcp/', api.mcp_endpoint, name='mcp_endpoint'),
    path('api/mcp', api.mcp_endpoint, name='mcp_endpoint_noslash'),
]
