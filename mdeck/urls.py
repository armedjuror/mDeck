from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView

from decks.sitemap import DeckSitemap, StaticSitemap

_sitemaps = {
    'decks': DeckSitemap,
    'static': StaticSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('allauth.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    path('', include('decks.urls')),
]
