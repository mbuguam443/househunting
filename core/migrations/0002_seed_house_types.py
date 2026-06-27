from django.db import migrations

SEED_TYPES = [
    ('bedsitter', 'Bedsitter'),
    ('studio', 'Studio'),
    ('one_bedroom', 'One Bedroom'),
    ('two_bedroom', 'Two Bedroom'),
    ('three_bedroom', 'Three Bedroom'),
    ('four_bedroom', 'Four Bedroom+'),
    ('townhouse', 'Townhouse'),
    ('villa', 'Villa'),
]

def seed_house_types(apps, schema_editor):
    HouseType = apps.get_model('core', 'HouseType')
    for i, (slug, name) in enumerate(SEED_TYPES):
        HouseType.objects.get_or_create(slug=slug, defaults={'name': name, 'display_order': i})

def reverse_seed(apps, schema_editor):
    HouseType = apps.get_model('core', 'HouseType')
    HouseType.objects.filter(slug__in=[s for s, _ in SEED_TYPES]).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_house_types, reverse_seed),
    ]
