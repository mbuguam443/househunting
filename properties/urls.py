from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.property_list, name='list'),
    path('add/', views.property_create, name='create'),
    path('<int:pk>/edit/', views.property_update, name='update'),
    path('<int:pk>/delete/', views.property_delete, name='delete'),
]
