from django.db import models
from django.contrib.auth.models import User

class Unit(models.Model):
    HOUSE_TYPES = (
        ('bedsitter', 'Bedsitter'),
        ('one_bedroom', 'One Bedroom'),
        ('two_bedroom', 'Two Bedroom'),
        ('three_bedroom', 'Three Bedroom'),
        ('four_bedroom', 'Four Bedroom'),
        ('studio', 'Studio'),
    )
    STATUS_CHOICES = (
        ('vacant', 'Vacant'),
        ('occupied', 'Occupied'),
    )
    property = models.ForeignKey('properties.Property', on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=50)
    house_type = models.CharField(max_length=20, choices=HOUSE_TYPES)
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.IntegerField(default=1)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    floor = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='vacant')
    available_from = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='unit_images/', blank=True)
    image_2 = models.ImageField(upload_to='unit_images/', blank=True)
    image_3 = models.ImageField(upload_to='unit_images/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['property', 'unit_number']

    def __str__(self):
        return f"{self.property.name} - {self.unit_number}"

    def get_amenities_list(self):
        items = []
        if hasattr(self, 'amenities'):
            a = self.amenities
            if a.water: items.append('Water')
            if a.electricity: items.append('Electricity')
            if a.parking: items.append('Parking')
            if a.security: items.append('Security')
            if a.internet: items.append('Internet')
            if a.furnished: items.append('Furnished')
        return items

class UnitAmenity(models.Model):
    unit = models.OneToOneField(Unit, on_delete=models.CASCADE, related_name='amenities')
    water = models.BooleanField(default=False)
    electricity = models.BooleanField(default=False)
    parking = models.BooleanField(default=False)
    security = models.BooleanField(default=False)
    internet = models.BooleanField(default=False)
    furnished = models.BooleanField(default=False)

    def __str__(self):
        return f"Amenities for {self.unit}"
