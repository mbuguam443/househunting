from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.portal_home, name='home'),
    path('payments/', views.portal_payments, name='payments'),
    path('pay/', views.portal_pay, name='pay'),
    path('maintenance/', views.portal_maintenance, name='maintenance'),
]
