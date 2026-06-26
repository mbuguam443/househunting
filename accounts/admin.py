from django.contrib import admin
from .models import Profile, PlatformConfig

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']

@admin.register(PlatformConfig)
class PlatformConfigAdmin(admin.ModelAdmin):
    list_display = ['fee_per_unit', 'trial_days', 'callback_url']
