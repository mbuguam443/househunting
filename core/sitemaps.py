from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from units.models import Unit
from website.models import AdminListing


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['website:home', 'website:browse', 'website:about', 'website:contact']

    def location(self, item):
        return reverse(item)


class UnitSitemap(Sitemap):
    priority = 0.6
    changefreq = 'daily'

    def items(self):
        return Unit.objects.filter(status='vacant').select_related('property')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/house/{obj.pk}/'


class AdminListingSitemap(Sitemap):
    priority = 0.6
    changefreq = 'daily'

    def items(self):
        return AdminListing.objects.filter(status='available')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return f'/house/{obj.pk}/'