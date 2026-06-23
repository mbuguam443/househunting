from django.urls import path
from . import views

urlpatterns = [
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('stk-push/', views.stk_push_view, name='stk_push'),
]
