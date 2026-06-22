import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.cache import cache_control
from django.shortcuts import render

MANIFEST = {
    "name": "PataNyumba",
    "short_name": "PataNyumba",
    "description": "Find your next home in Kenya. Browse rental properties, apartments, and houses across the country.",
    "start_url": "/",
    "display": "standalone",
    "orientation": "portrait-primary",
    "theme_color": "#6a4cdb",
    "background_color": "#121212",
    "categories": ["real estate", "rental", "housing"],
    "lang": "en-KE",
    "icons": [
        {"src": "/static/img/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/static/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
    "screenshots": [],
}


def manifest(request):
    return JsonResponse(MANIFEST, json_dumps_params={'indent': 2})


@cache_control(max_age=0, no_cache=True, no_store=True, must_revalidate=True)
def service_worker(request):
    return render(request, 'sw.js', content_type='application/javascript')
