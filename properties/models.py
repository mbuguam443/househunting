from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=200)
    description = models.TextField()
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    estate = models.CharField(max_length=200, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'properties'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def total_units(self):
        return self.units.count()

    def vacant_units(self):
        return self.units.filter(status='vacant').count()

    def occupied_units(self):
        return self.units.filter(status='occupied').count()
