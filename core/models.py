from django.db import models

class HouseType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text='Display name, e.g. "Single Room"')
    slug = models.SlugField(max_length=50, unique=True, help_text='URL slug, e.g. "single_room"')
    display_order = models.IntegerField(default=0, help_text='Sort order in dropdowns')

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'House Type'
        verbose_name_plural = 'House Types'

    def __str__(self):
        return self.name
