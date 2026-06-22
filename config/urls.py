from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
