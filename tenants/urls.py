from django.urls import path
from . import views

app_name = 'tenants'

urlpatterns = [
    path('', views.tenant_list, name='list'),
    path('register/', views.register_tenant, name='register'),
    path('create/', views.tenant_create, name='create'),
    path('<int:pk>/', views.tenant_detail, name='detail'),
    path('<int:pk>/vacate/', views.tenant_vacate, name='vacate'),
    path('rent-collection/', views.rent_collection, name='rent_collection'),
    path('payments/<int:pk>/mark-paid/', views.mark_paid, name='mark_paid'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('maintenance/<int:pk>/update/', views.maintenance_update, name='maintenance_update'),
    path('lease/create/<int:tenancy_pk>/', views.lease_create, name='lease_create'),
    path('lease/<int:pk>/', views.lease_detail, name='lease_detail'),
    path('lease/<int:pk>/accept/', views.lease_accept, name='lease_accept'),
    path('lease/<int:pk>/terminate/', views.lease_terminate, name='lease_terminate'),
]
