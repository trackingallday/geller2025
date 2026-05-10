from django.db import migrations


def set_wall_chart_color(apps, schema_editor):
    # Geller brand purple from the Product user guide PDF header
    Product = apps.get_model('chemsapp', 'Product')
    Product.objects.filter(wall_chart_color__isnull=True).update(wall_chart_color='#6B3FA0')
    Product.objects.filter(wall_chart_color='').update(wall_chart_color='#6B3FA0')


def unset_wall_chart_color(apps, schema_editor):
    Product = apps.get_model('chemsapp', 'Product')
    Product.objects.filter(wall_chart_color='#6B3FA0').update(wall_chart_color=None)


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0013_product_wall_chart_color'),
    ]

    operations = [
        migrations.RunPython(set_wall_chart_color, unset_wall_chart_color),
    ]
