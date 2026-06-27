from django.db import migrations, models
import django.db.models.deletion

def populate_house_type_fk(apps, schema_editor):
    Unit = apps.get_model('units', 'Unit')
    HouseType = apps.get_model('core', 'HouseType')
    # Map old slug values to house types
    slug_map = {
        'bedsitter': 'bedsitter', 'studio': 'studio',
        'one_bedroom': 'one_bedroom', 'two_bedroom': 'two_bedroom',
        'three_bedroom': 'three_bedroom', 'four_bedroom': 'four_bedroom',
    }
    for unit in Unit.objects.all():
        slug = unit.house_type_old
        ht = HouseType.objects.filter(slug=slug).first()
        if ht:
            unit.house_type = ht
            unit.save(update_fields=['house_type'])

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_seed_house_types'),
        ('units', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='unit',
            old_name='house_type',
            new_name='house_type_old',
        ),
        migrations.AddField(
            model_name='unit',
            name='house_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='units', to='core.housetype'),
        ),
        migrations.RunPython(populate_house_type_fk, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='unit',
            name='house_type_old',
        ),
        migrations.AlterField(
            model_name='unit',
            name='house_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='units', to='core.housetype'),
        ),
    ]
