from django.core.management.base import BaseCommand
from properties.models import Property
from website.models import AdminListing
from urllib.request import urlopen
from urllib.parse import quote
import json


def geocode(address):
    url = f'https://nominatim.openstreetmap.org/search?format=json&q={quote(address)}&limit=1&countrycodes=ke'
    try:
        resp = urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data:
            return float(data[0]['lat']), float(data[0]['lon'])
    except Exception:
        pass
    return None, None


class Command(BaseCommand):
    help = 'Backfill lat/lng for properties and admin listings without coordinates'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be updated')

    def handle(self, *args, **options):
        dry = options['dry_run']

        for prop in Property.objects.filter(latitude__isnull=True):
            parts = [p for p in [prop.estate, prop.town, prop.county, 'Kenya'] if p]
            address = ', '.join(parts)
            lat, lng = geocode(address)
            if lat and lng:
                if dry:
                    self.stdout.write(f'[DRY] Property {prop.pk} ({prop.name}): {lat}, {lng}')
                else:
                    prop.latitude = lat
                    prop.longitude = lng
                    prop.save(update_fields=['latitude', 'longitude'])
                    self.stdout.write(f'Property {prop.pk} ({prop.name}): {lat}, {lng}')
            else:
                self.stdout.write(f'Could not geocode Property {prop.pk} ({prop.name}): {address}')

        for listing in AdminListing.objects.filter(latitude__isnull=True):
            parts = [p for p in [listing.estate, listing.town, listing.county, 'Kenya'] if p]
            address = ', '.join(parts)
            lat, lng = geocode(address)
            if lat and lng:
                if dry:
                    self.stdout.write(f'[DRY] AdminListing {listing.pk} ({listing.title}): {lat}, {lng}')
                else:
                    listing.latitude = lat
                    listing.longitude = lng
                    listing.save(update_fields=['latitude', 'longitude'])
                    self.stdout.write(f'AdminListing {listing.pk} ({listing.title}): {lat}, {lng}')
            else:
                self.stdout.write(f'Could not geocode AdminListing {listing.pk} ({listing.title}): {address}')
