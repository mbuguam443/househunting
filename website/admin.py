from django.contrib import admin
from .models import Inquiry, Testimonial, Faq

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit', 'email', 'is_read', 'created_at']
    list_filter = ['is_read']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'is_active']

@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ['question', 'order', 'is_active']
    list_filter = ['is_active']
