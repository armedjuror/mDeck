from django.contrib import admin

from .models import APIKey, Category, Deck, DeckVersion, Profile, Theme


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at']
    raw_id_fields = ['user']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent', 'created_at']
    list_filter = ['user']
    raw_id_fields = ['user', 'parent']


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'bg', 'text', 'accent']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'theme', 'view_count', 'updated_at']
    list_filter = ['status', 'theme']
    search_fields = ['title', 'tags', 'owner__email']
    raw_id_fields = ['owner', 'category']
    actions = ['approve_decks', 'reject_decks']

    def approve_decks(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} deck(s) approved and published.')
    approve_decks.short_description = 'Approve selected decks (publish)'

    def reject_decks(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} deck(s) rejected (set to draft).')
    reject_decks.short_description = 'Reject selected decks (set to draft)'


@admin.register(DeckVersion)
class DeckVersionAdmin(admin.ModelAdmin):
    list_display = ['deck', 'saved_at']
    raw_id_fields = ['deck']


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ['user', 'name', 'prefix', 'created_at', 'last_used']
    raw_id_fields = ['user']
