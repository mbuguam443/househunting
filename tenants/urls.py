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
    path('record-payment/', views.record_payment, name='record_payment'),
    path('reports/', views.reports, name='reports'),
    path('c2b-transactions/', views.c2b_transactions, name='c2b_transactions'),
    path('utilities/', views.utility_list, name='utility_list'),
    path('utilities/add/', views.utility_add, name='utility_add'),
    path('utilities/<int:pk>/edit/', views.utility_edit, name='utility_edit'),
    path('utilities/<int:pk>/delete/', views.utility_delete, name='utility_delete'),
    path('utilities/<int:pk>/toggle/', views.utility_mark_paid, name='utility_mark_paid'),
    path('b2c/pay/', views.b2c_pay, name='b2c_pay'),
    path('b2c/history/', views.b2c_history, name='b2c_history'),
    path('b2c/settings/', views.b2c_settings, name='b2c_settings'),
    path('b2c/result/', views.b2c_result, name='b2c_result'),
    path('b2c/timeout/', views.b2c_timeout, name='b2c_timeout'),
]
