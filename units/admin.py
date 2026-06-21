from django.contrib import admin
from .models import Unit, UnitAmenity

class UnitAmenityInline(admin.StackedInline):
    model = UnitAmenity

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'property', 'house_type', 'monthly_rent', 'status', 'bedrooms']
    list_filter = ['status', 'house_type', 'property']
    search_fields = ['unit_number', 'property__name']
    inlines = [UnitAmenityInline]

@admin.register(UnitAmenity)
class UnitAmenityAdmin(admin.ModelAdmin):
    list_display = ['unit', 'water', 'electricity', 'parking', 'security']
