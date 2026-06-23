from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from properties.models import Property
from units.models import Unit, UnitAmenity
from website.models import Testimonial, Faq
from tenants.rent_utils import generate_rent_payments

class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        if User.objects.filter(username='admin').exists():
            self.stdout.write(self.style.WARNING('Data already seeded. Skipping.'))
            return

        admin = User.objects.create_superuser('admin', 'admin@patanyumba.co.ke', 'admin123')
        admin.first_name = 'Admin'
        admin.save()
        admin.profile.role = 'landlord'
        admin.profile.phone = '+254 700 000 000'
        admin.profile.save()

        tenant_user = User.objects.create_user('johndoe', 'john@email.com', 'password123')
        tenant_user.first_name = 'John'
        tenant_user.last_name = 'Doe'
        tenant_user.save()
        tenant_user.profile.role = 'tenant'
        tenant_user.profile.phone = '+254 712 345 678'
        tenant_user.profile.save()

        prop1 = Property.objects.create(
            owner=admin, name='Green Valley Apartments',
            description='Modern apartment complex in the heart of Kilimani. Well-maintained compound with ample parking, 24-hour security, and close to shopping centers.',
            county='Nairobi', town='Kilimani', estate='Woodley Estate',
        )
        prop2 = Property.objects.create(
            owner=admin, name='Sunrise Court',
            description='Quiet residential area with easy access to Mombasa Road. Ideal for families.',
            county='Nairobi', town='South B', estate='Madaraka Estate',
        )
        prop3 = Property.objects.create(
            owner=admin, name='Mountain View Residences',
            description='Premium units with stunning views of Mt. Kenya. Serene environment perfect for remote work.',
            county='Nyeri', town='Nyeri Town', estate='Milimani',
        )

        units_data = [
            (prop1, 'A1', 'one_bedroom', 1, 1, 15000, 15000, 2, 'Spacious one-bedroom with balcony overlooking the courtyard. Tiled floors, fitted kitchen with granite countertops.', {'water': True, 'electricity': True, 'parking': True, 'security': True}),
            (prop1, 'A2', 'one_bedroom', 1, 1, 15000, 15000, 2, 'Similar to A1 but with larger living room. Ample closet space.', {'water': True, 'electricity': True, 'parking': True, 'security': True}),
            (prop1, 'B1', 'two_bedroom', 2, 1, 25000, 25000, 3, 'Two-bedroom unit with master ensuite. Spacious living and dining area.', {'water': True, 'electricity': True, 'parking': True, 'security': True, 'internet': True}),
            (prop1, 'B2', 'two_bedroom', 2, 1, 25000, 25000, 3, 'Corner unit with extra windows, lots of natural light.', {'water': True, 'electricity': True, 'parking': True, 'security': True}),
            (prop1, 'C1', 'bedsitter', 1, 1, 8000, 8000, 1, 'Affordable bedsitter. Tiled floors, kitchen area, and bathroom.', {'water': True, 'electricity': True, 'security': True}),
            (prop2, '1A', 'one_bedroom', 1, 1, 12000, 12000, 1, 'Ground floor one-bedroom with small garden access. Freshly painted.', {'water': True, 'electricity': True, 'security': True}),
            (prop2, '1B', 'two_bedroom', 2, 1, 18000, 18000, 1, 'Two-bedroom ground floor unit. Walking distance to supermarket.', {'water': True, 'electricity': True, 'parking': True, 'security': True}),
            (prop2, '2A', 'bedsitter', 1, 1, 6500, 6500, 2, 'Budget-friendly bedsitter. Water and basic electricity included.', {'water': True, 'electricity': True, 'security': True}),
            (prop2, '2B', 'studio', 1, 1, 10000, 10000, 2, 'Modern studio apartment with open-plan living. Fitted kitchen.', {'water': True, 'electricity': True, 'security': True, 'internet': True, 'furnished': True}),
            (prop3, 'MV1', 'two_bedroom', 2, 2, 22000, 22000, 1, 'Premium two-bedroom with mountain views. Both rooms are ensuite.', {'water': True, 'electricity': True, 'parking': True, 'security': True, 'internet': True}),
            (prop3, 'MV2', 'one_bedroom', 1, 1, 14000, 14000, 1, 'Cozy one-bedroom with heated water. Perfect for couples.', {'water': True, 'electricity': True, 'parking': True, 'security': True}),
            (prop3, 'MV3', 'three_bedroom', 3, 2, 35000, 35000, 2, 'Spacious three-bedroom family unit with balcony. Staff quarters included.', {'water': True, 'electricity': True, 'parking': True, 'security': True, 'internet': True, 'furnished': True}),
        ]

        for prop, unit_no, htype, beds, baths, rent, dep, floor, desc, amenities in units_data:
            unit = Unit.objects.create(
                property=prop, unit_number=unit_no, house_type=htype,
                bedrooms=beds, bathrooms=baths, monthly_rent=rent,
                deposit=dep, floor=floor, description=desc, status='vacant',
            )
            UnitAmenity.objects.create(unit=unit, **amenities)

        # Mark some units as occupied
        for unit_no in ['A1', 'B1', '1A', '2B', 'MV2']:
            Unit.objects.filter(unit_number=unit_no).update(status='occupied')

        # Create tenancy for johndoe demo tenant
        from tenants.models import Tenancy
        from datetime import date
        tenant_user = User.objects.get(username='johndoe')
        demo_unit = Unit.objects.get(unit_number='A1')
        Tenancy.objects.get_or_create(
            tenant=tenant_user, unit=demo_unit,
            defaults=dict(start_date=date(2026, 1, 1), monthly_rent=demo_unit.monthly_rent, deposit_paid=25000, status='active'),
        )
        generate_rent_payments()

        Testimonial.objects.create(
            name='Grace Wambui', role='Tenant, Nairobi',
            content='PataNyumba made finding my new home so easy. I browsed, compared, and connected with the landlord all in one day!',
            is_active=True,
        )
        Testimonial.objects.create(
            name='Peter Kamau', role='Landlord, Nyeri',
            content='Managing my properties has never been easier. The dashboard shows me everything at a glance and my vacant units get seen instantly.',
            is_active=True,
        )
        Testimonial.objects.create(
            name='Mary Achieng', role='Tenant, Mombasa',
            content='I was tired of dealing with agents. PataNyumba let me connect directly with the landlord. Highly recommend!',
            is_active=True,
        )

        Faq.objects.create(question='How do I search for available houses?', answer='Use the search bar on the homepage or browse all listings. You can filter by location, house type, bedrooms, and rent range.', order=1, is_active=True)
        Faq.objects.create(question='Do I need an account to browse houses?', answer='No, you can browse all vacant units without creating an account. You only need to register if you want to send an inquiry or if you are a landlord managing properties.', order=2, is_active=True)
        Faq.objects.create(question='Is PataNyumba free for tenants?', answer='Yes! PataNyumba is completely free for tenants. You can browse, inquire, and find your next home without paying any fees.', order=3, is_active=True)
        Faq.objects.create(question='How do I list my property as a landlord?', answer='Register as a landlord, add your property and units, and they will automatically appear on the public website when marked as vacant.', order=4, is_active=True)
        Faq.objects.create(question='How do I mark a unit as occupied?', answer='From your dashboard, assign a tenant to the unit. The unit will automatically switch from vacant to occupied and disappear from public listings.', order=5, is_active=True)
        Faq.objects.create(question='Can I edit or delete my listings?', answer='Yes, you can edit or delete your properties and units at any time from the dashboard.', order=6, is_active=True)

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(f'  Admin: admin / admin123')
        self.stdout.write(f'  Tenant: johndoe / password123')
