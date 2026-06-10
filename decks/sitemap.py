from django.contrib.sitemaps import Sitemap

from .models import Deck


class DeckSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    protocol = 'https'

    def items(self):
        return Deck.objects.filter(status='published').order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/explore/{obj.slug}/'


class StaticSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    protocol = 'https'

    def items(self):
        return ['/', '/explore/']

    def location(self, item):
        return item
