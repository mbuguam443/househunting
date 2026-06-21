from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'county', 'town', 'total_units', 'vacant_units']
    list_filter = ['county', 'town']
    search_fields = ['name', 'town', 'estate']
