from django.contrib import admin
from .models import HouseType

@admin.register(HouseType)
class HouseTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_order']
    list_editable = ['display_order']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']