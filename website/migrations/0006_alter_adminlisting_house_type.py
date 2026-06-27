from django.db import migrations, models
import django.db.models.deletion

def populate_house_type_fk(apps, schema_editor):
    AdminListing = apps.get_model('website', 'AdminListing')
    HouseType = apps.get_model('core', 'HouseType')
    slug_map = {
        'bedsitter': 'bedsitter', 'studio': 'studio',
        'one_bedroom': 'one_bedroom', 'two_bedroom': 'two_bedroom',
        'three_bedroom': 'three_bedroom', 'four_bedroom': 'four_bedroom+',
        'townhouse': 'townhouse', 'villa': 'villa',
    }
    for listing in AdminListing.objects.all():
        slug = listing.house_type_old
        ht = HouseType.objects.filter(slug=slug).first()
        if ht:
            listing.house_type = ht
            listing.save(update_fields=['house_type'])

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_house_types'),
        ('website', '0005_adminlisting_latitude_adminlisting_longitude'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adminlisting',
            old_name='house_type',
            new_name='house_type_old',
        ),
        migrations.AddField(
            model_name='adminlisting',
            name='house_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='admin_listings', to='core.housetype'),
        ),
        migrations.RunPython(populate_house_type_fk, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='adminlisting',
            name='house_type_old',
        ),
        migrations.AlterField(
            model_name='adminlisting',
            name='house_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='admin_listings', to='core.housetype'),
        ),
    ]
