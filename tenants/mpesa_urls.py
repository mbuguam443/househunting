from django.urls import path
from . import views

urlpatterns = [
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('stk-push/<int:payment_id>/', views.stk_push_view, name='stk_push'),
]
