from django.urls import path
from django.http import HttpResponse


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Disallow: /admin/',
        'Disallow: /accounts/',
        'Disallow: /dashboard/',
        'Disallow: /portal/',
        'Disallow: /mpesa/',
        'Disallow: /properties/',
        'Disallow: /units/',
        '',
        'Sitemap: https://patanyumba.co.ke/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


urlpatterns = [
    path('', robots_txt, name='robots_txt'),
]