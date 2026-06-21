from django.urls import path
from . import views

app_name = 'units'

urlpatterns = [
    path('', views.unit_list, name='list'),
    path('add/', views.unit_create, name='create'),
    path('<int:pk>/edit/', views.unit_update, name='update'),
    path('<int:pk>/delete/', views.unit_delete, name='delete'),
    path('vacancies/', views.vacancies, name='vacancies'),
]
