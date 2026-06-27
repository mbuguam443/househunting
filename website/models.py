from django.db import models

class Inquiry(models.Model):
    unit = models.ForeignKey('units.Unit', null=True, blank=True, on_delete=models.CASCADE, related_name='inquiries')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.unit}"

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    avatar = models.ImageField(upload_to='testimonials/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Faq(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order']

    def __str__(self):
        return self.question


class AdminListing(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'), ('rented', 'Rented'), ('withdrawn', 'Withdrawn'),
    ]
    title = models.CharField(max_length=200, help_text='e.g. Furnished 1BR in Kilimani')
    description = models.TextField()
    county = models.CharField(max_length=100)
    town = models.CharField(max_length=100)
    estate = models.CharField(max_length=200, blank=True)
    house_type = models.ForeignKey('core.HouseType', on_delete=models.PROTECT, related_name='admin_listings')
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    rent = models.DecimalField(max_digits=10, decimal_places=2, help_text='Monthly rent in KES')
    contact_name = models.CharField(max_length=100, blank=True, help_text='Landlord or agent name')
    contact_phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='admin_listings/', blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Listing'

    def __str__(self):
        return f'{self.title} — KES {self.rent}'


class AdminListingImage(models.Model):
    listing = models.ForeignKey(AdminListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='admin_listings/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Image {self.order} for {self.listing.title}'
