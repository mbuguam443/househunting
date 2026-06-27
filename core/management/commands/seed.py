from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile, SubscriptionPlan, PlatformConfig, LandlordSubscription
from core.models import HouseType
from properties.models import Property
from units.models import Unit, UnitAmenity
from website.models import Testimonial, Faq
from tenants.models import Tenancy, LeaseAgreement
from tenants.rent_utils import generate_rent_payments
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone


class Command(BaseCommand):
    help = 'Seed database with initial data'

    def handle(self, *args, **options):
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults=dict(is_superuser=True, is_staff=True, email='admin@patanyumba.co.ke'),
        )
        admin.set_password('admin123')
        if _:
            admin.first_name = 'Admin'
        admin.save()
        admin.profile.role = 'admin'
        admin.profile.phone = '+254 700 000 000'
        admin.profile.save()

        PlatformConfig.objects.get_or_create(pk=1, defaults={'fee_per_unit': 50.00})

        # --- Landlord: Grace (KES 50/unit, paid subscription) ---
        grace, _ = User.objects.get_or_create(
            username='grace',
            defaults=dict(email='grace@email.com'),
        )
        grace.set_password('grace123')
        if _:
            grace.first_name = 'Grace'
            grace.last_name = 'Kamau'
        grace.save()
        grace.profile.role = 'landlord'
        grace.profile.phone = '+254 722 111 111'
        grace.profile.fee_per_unit = 50.00
        grace.profile.trial_started_at = timezone.now()
        grace.profile.save()

        # Assign Sunrise Court to Grace
        Property.objects.filter(name='Sunrise Court').update(owner=grace)

        LandlordSubscription.objects.get_or_create(
            landlord=grace,
            defaults=dict(
                unit_count=4,
                amount=200,
                start_date=date(2026, 6, 1),
                end_date=date(2026, 8, 31),
                status='active',
                notes='4 units × KES 50/unit × 3 months',
            ),
        )

        # --- Landlord: Peter (fee=0, free service, no subscription) ---
        peter, _ = User.objects.get_or_create(
            username='peter',
            defaults=dict(email='peter@email.com'),
        )
        peter.set_password('peter123')
        if _:
            peter.first_name = 'Peter'
            peter.last_name = 'Mwangi'
        peter.save()
        peter.profile.role = 'landlord'
        peter.profile.phone = '+254 733 222 222'
        peter.profile.fee_per_unit = 0.00
        peter.profile.save()

        # Assign Mountain View Residences to Peter
        Property.objects.filter(name='Mountain View Residences').update(owner=peter)

        for plan_name, amt, days, desc in [
            ('Monthly', 500, 30, '30 days of platform access'),
            ('Quarterly', 1200, 90, '90 days — save 20%'),
            ('Yearly', 4000, 365, 'Full year — save 33%'),
        ]:
            SubscriptionPlan.objects.get_or_create(name=plan_name, defaults=dict(amount=amt, duration_days=days, description=desc))

        tenant_user, _ = User.objects.get_or_create(
            username='johndoe',
            defaults=dict(email='john@email.com'),
        )
        tenant_user.set_password('password123')
        if _:
            tenant_user.first_name = 'John'
            tenant_user.last_name = 'Doe'
        tenant_user.save()
        tenant_user.profile.role = 'tenant'
        tenant_user.profile.phone = '+254 712 345 678'
        tenant_user.profile.save()

        prop1, _ = Property.objects.get_or_create(
            name='Green Valley Apartments',
            defaults=dict(
                owner=admin,
                description='Modern apartment complex in the heart of Kilimani. Well-maintained compound with ample parking, 24-hour security, and close to shopping centers.',
                county='Nairobi', town='Kilimani', estate='Woodley Estate',
            ),
        )
        prop2, _ = Property.objects.get_or_create(
            name='Sunrise Court',
            defaults=dict(
                owner=admin,
                description='Quiet residential area with easy access to Mombasa Road. Ideal for families.',
                county='Nairobi', town='South B', estate='Madaraka Estate',
            ),
        )
        prop3, _ = Property.objects.get_or_create(
            name='Mountain View Residences',
            defaults=dict(
                owner=admin,
                description='Premium units with stunning views of Mt. Kenya. Serene environment perfect for remote work.',
                county='Nyeri', town='Nyeri Town', estate='Milimani',
            ),
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

        ht_cache = {ht.slug: ht for ht in HouseType.objects.all()}
        for prop, unit_no, htype, beds, baths, rent, dep, floor, desc, amenities in units_data:
            unit, _ = Unit.objects.get_or_create(
                property=prop, unit_number=unit_no,
                defaults=dict(
                    house_type=ht_cache[htype], bedrooms=beds, bathrooms=baths,
                    monthly_rent=rent, deposit=dep, floor=floor,
                    description=desc, status='vacant',
                ),
            )
            UnitAmenity.objects.get_or_create(unit=unit, defaults=amenities)

        # Additional tenant users
        tenant_data = [
            ('janewanjiku', 'Jane', 'Wanjiku', 'password123', '+254 712 345 679'),
            ('bobkiarie', 'Bob', 'Kiarie', 'password123', '+254 712 345 680'),
            ('alicemuthoni', 'Alice', 'Muthoni', 'password123', '+254 712 345 681'),
            ('davidotieno', 'David', 'Otieno', 'password123', '+254 712 345 682'),
            ('sarahchebet', 'Sarah', 'Chebet', 'password123', '+254 712 345 683'),
            ('jamesmwangi', 'James', 'Mwangi', 'password123', '+254 712 345 684'),
            ('faithnyambura', 'Faith', 'Nyambura', 'password123', '+254 712 345 685'),
            ('peterowino', 'Peter', 'Owino', 'password123', '+254 712 345 686'),
            ('marywangui', 'Mary', 'Wangui', 'password123', '+254 712 345 687'),
            ('kevinmutua', 'Kevin', 'Mutua', 'password123', '+254 712 345 688'),
            ('estherwambui', 'Esther', 'Wambui', 'password123', '+254 712 345 689'),
        ]
        tenant_map = {'johndoe': tenant_user}
        for uname, fn, ln, pw, phone in tenant_data:
            u, _ = User.objects.get_or_create(username=uname, defaults=dict(email=f'{uname}@email.com'))
            u.set_password(pw)
            if _:
                u.first_name = fn
                u.last_name = ln
            u.save()
            u.profile.role = 'tenant'
            u.profile.phone = phone
            u.profile.save()
            tenant_map[uname] = u

        # Reset all units to vacant, then mark only desired ones as occupied
        Unit.objects.all().update(status='vacant')
        Tenancy.objects.all().delete()
        # Occupied units with assigned tenants (C1, 1B, MV3 left vacant)
        unit_tenants = {
            'A1': 'johndoe', 'A2': 'janewanjiku', 'B1': 'bobkiarie', 'B2': 'alicemuthoni',
            '1A': 'sarahchebet', '2A': 'faithnyambura', '2B': 'peterowino',
            'MV1': 'marywangui', 'MV2': 'kevinmutua',
        }
        for unit_no, uname in unit_tenants.items():
            Unit.objects.filter(unit_number=unit_no).update(status='occupied')
            unit = Unit.objects.get(unit_number=unit_no)
            Tenancy.objects.get_or_create(
                tenant=tenant_map[uname], unit=unit,
                defaults=dict(
                    start_date=date(2026, 1, 1) if unit_no in ('A1', 'A2', 'B1', 'B2') else date(2026, 3, 1),
                    monthly_rent=unit.monthly_rent,
                    deposit_paid=unit.monthly_rent * Decimal('1.5'),
                    status='active',
                ),
            )
        # Create a demo lease for John Doe
        jd_tenancy = Tenancy.objects.filter(tenant=tenant_map['johndoe']).first()
        if jd_tenancy and not hasattr(jd_tenancy, 'lease'):
            LeaseAgreement.objects.create(
                tenancy=jd_tenancy,
                start_date=date(2026, 1, 1),
                end_date=date(2026, 12, 31),
                monthly_rent=jd_tenancy.monthly_rent,
                deposit_amount=jd_tenancy.deposit_paid,
                payment_due_day=5,
                late_fee=500,
                notice_period_days=30,
                terms='1. Rent is due on or before the 5th of every month.\n2. A late fee of KES 500 applies for payments received after the due date.\n3. The tenant shall not sublet the premises without written consent from the landlord.\n4. The landlord shall maintain the premises in habitable condition.\n5. Either party may terminate this agreement with 30 days written notice.\n6. The tenant is responsible for water and electricity bills.\n7. No structural alterations without prior written approval.',
                status='active',
                landlord_accepted=True,
                landlord_accepted_at=timezone.now(),
                tenant_accepted=False,
            )
        generate_rent_payments()

        Testimonial.objects.get_or_create(
            name='Grace Wambui',
            defaults=dict(
                role='Tenant, Nairobi',
                content='PataNyumba made finding my new home so easy. I browsed, compared, and connected with the landlord all in one day!',
                is_active=True,
            ),
        )
        Testimonial.objects.get_or_create(
            name='Peter Kamau',
            defaults=dict(
                role='Landlord, Nyeri',
                content='Managing my properties has never been easier. The dashboard shows me everything at a glance and my vacant units get seen instantly.',
                is_active=True,
            ),
        )
        Testimonial.objects.get_or_create(
            name='Mary Achieng',
            defaults=dict(
                role='Tenant, Mombasa',
                content='I was tired of dealing with agents. PataNyumba let me connect directly with the landlord. Highly recommend!',
                is_active=True,
            ),
        )

        for i, (q, a) in enumerate([
            ('How do I search for available houses?', 'Use the search bar on the homepage or browse all listings. You can filter by location, house type, bedrooms, and rent range.'),
            ('Do I need an account to browse houses?', 'No, you can browse all vacant units without creating an account. You only need to register if you want to send an inquiry or if you are a landlord managing properties.'),
            ('Is PataNyumba free for tenants?', 'Yes! PataNyumba is completely free for tenants. You can browse, inquire, and find your next home without paying any fees.'),
            ('How do I list my property as a landlord?', 'Register as a landlord, add your property and units, and they will automatically appear on the public website when marked as vacant.'),
            ('How do I mark a unit as occupied?', 'From your dashboard, assign a tenant to the unit. The unit will automatically switch from vacant to occupied and disappear from public listings.'),
            ('Can I edit or delete my listings?', 'Yes, you can edit or delete your properties and units at any time from the dashboard.'),
        ], 1):
            Faq.objects.get_or_create(question=q, defaults=dict(answer=a, order=i, is_active=True))

        from website.models import AdminListing
        ht_cache = {ht.slug: ht for ht in HouseType.objects.all()}
        listing_data = [
            ('Fully Furnished 1BR in Westlands', 'Modern one-bedroom apartment with WiFi, DStv connection, and gym access. Walking distance to Sarit Centre.', 'Nairobi', 'Westlands', 'Rhapta Road', 'one_bedroom', 1, 1, 28000, 'James K.', '+254 722 100 200'),
            ('Executive 2BR in Kilimani', 'Spacious two-bedroom on the 5th floor with panoramic city views. Open-plan living, fitted kitchen, and dedicated parking.', 'Nairobi', 'Kilimani', 'Kirichwa Road', 'two_bedroom', 2, 2, 45000, 'Mary W.', '+254 733 200 300'),
            ('Affordable Bedsitter in Ruiru', 'Clean bedsitter with water and electricity included. Secure compound with gatekeeper.', 'Kiambu', 'Ruiru', 'Kenyatta Road', 'bedsitter', 1, 1, 6500, 'Esther N.', '+254 711 300 400'),
            ('3BR Townhouse in Syokimau', 'Beautiful townhouse in a gated community. 24-hour security, kids play area, adjacent to shopping mall.', 'Machakos', 'Syokimau', 'Old Mombasa Road', 'three_bedroom', 3, 2, 55000, 'Peter O.', '+254 722 400 500'),
            ('Studio Unit in Thika Town', 'Cozy studio with kitchenette and separate bathroom. Walking distance to Thika Mall. Great for students.', 'Kiambu', 'Thika', 'Town Centre', 'studio', 1, 1, 9500, 'Grace K.', '+254 733 500 600'),
        ]
        admin_user = User.objects.get(username='admin')
        for title, desc, county, town, estate, htype, beds, baths, rent, contact_name, contact_phone in listing_data:
            AdminListing.objects.get_or_create(
                title=title,
                defaults=dict(
                    description=desc, county=county, town=town, estate=estate,
                    house_type=ht_cache[htype], bedrooms=beds, bathrooms=baths, rent=rent,
                    contact_name=contact_name, contact_phone=contact_phone,
                    status='available', created_by=admin_user,
                ),
            )

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
        self.stdout.write(f'  Admin: admin / admin123')
        self.stdout.write(f'  Landlord: grace / grace123 (KES 50/unit, paid)')
        self.stdout.write(f'  Landlord: peter / peter123 (Free, KES 0)')
        self.stdout.write(f'  Tenants: johndoe, janewanjiku, bobkiarie, alicemuthoni, davidotieno,')
        self.stdout.write(f'          sarahchebet, jamesmwangi, faithnyambura, peterowino,')
        self.stdout.write(f'          marywangui, kevinmutua, estherwambui')
        self.stdout.write(f'          (all password: password123)')
