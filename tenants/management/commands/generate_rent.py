from django.core.management.base import BaseCommand
from tenants.rent_utils import generate_rent_payments, mark_overdue_payments


class Command(BaseCommand):
    help = 'Generate monthly rent invoices and mark overdue payments'

    def add_arguments(self, parser):
        parser.add_argument('--landlord', type=int, help='Limit to a specific landlord user ID')

    def handle(self, *args, **options):
        landlord_id = options.get('landlord')
        landlord = None
        if landlord_id:
            from django.contrib.auth.models import User
            landlord = User.objects.get(pk=landlord_id)

        created = generate_rent_payments(landlord=landlord)
        marked = mark_overdue_payments(landlord=landlord)
        self.stdout.write(self.style.SUCCESS(f'Created {created} rent payment(s), marked {marked} overdue'))
