from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/landlords/', views.admin_landlords, name='admin_landlords'),
    path('admin/landlords/create/', views.admin_create_landlord, name='admin_create_landlord'),
    path('admin/landlords/<int:landlord_id>/subscription/', views.admin_assign_subscription, name='admin_assign_sub'),
    path('admin/landlords/<int:landlord_id>/set-fee/', views.admin_set_landlord_fee, name='admin_set_fee'),
    path('admin/plans/', views.admin_subscription_plans, name='admin_plans'),
    path('admin/plans/create/', views.admin_plan_create, name='admin_plan_create'),
    path('admin/plans/<int:pk>/toggle/', views.admin_plan_toggle, name='admin_plan_toggle'),
    path('admin/revenue/', views.admin_revenue, name='admin_revenue'),
    path('admin/update-fee/', views.admin_update_fee, name='admin_update_fee'),
]
