from django.urls import path
from . import views

app_name = 'website'

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('house/<int:pk>/', views.house_detail, name='house_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
