from django.urls import path
from . import views

urlpatterns = [
    path('callback/', views.mpesa_callback, name='mpesa_callback'),
    path('stk-push/', views.stk_push_view, name='stk_push'),
    path('check-status/', views.check_payment_status, name='check_status'),
    path('query/<int:payment_id>/', views.query_stk_push, name='query_stk'),
]
