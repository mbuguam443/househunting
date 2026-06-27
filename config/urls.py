from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.contrib.sitemaps.views import sitemap
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView
from website import pwa as pwa_views
from core.sitemaps import StaticViewSitemap, UnitSitemap, AdminListingSitemap
from tenants import views as tenant_views

sitemaps = {
    'static': StaticViewSitemap,
    'units': UnitSitemap,
    'listings': AdminListingSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('properties/', include('properties.urls')),
    path('units/', include('units.urls')),
    path('dashboard/tenants/', include('tenants.urls')),
    path('portal/', include('tenants.portal_urls')),
    path('mpesa/', include('tenants.mpesa_urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', include('website.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', include('core.urls')),
    path('manifest.json', pwa_views.manifest),
    path('sw.js', pwa_views.service_worker),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    # C2B callbacks — clean path (Safaricom may reject URLs with /mpesa/)
    path('c2b/confirmation/', tenant_views.c2b_confirmation, name='c2b_confirmation'),
    path('c2b/validation/', tenant_views.c2b_validation, name='c2b_validation'),
]
