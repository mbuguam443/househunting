from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from website import pwa as pwa_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('properties/', include('properties.urls')),
    path('units/', include('units.urls')),
    path('dashboard/tenants/', include('tenants.urls')),
    path('portal/', include('tenants.portal_urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', include('website.urls')),
    path('manifest.json', pwa_views.manifest),
    path('sw.js', pwa_views.service_worker),
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
