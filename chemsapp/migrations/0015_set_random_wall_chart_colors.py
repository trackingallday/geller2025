import random
from django.db import migrations


# Pastel background colours from the Geller Product User Guide PDF
WALL_CHART_COLORS = [
    '#e8f0d8',  # light green (Ultimo Pot & Pan / Lime Off)
    '#e8eaf0',  # light blue-grey (Ultimo Auto Dishwasher Detergent)
    '#f5e8e8',  # light rose/pink (Ultimo Raider Floor Cleaner)
    '#fdf0e0',  # light peach/orange (Ultimo.2 HD Degreaser)
    '#fce8ec',  # light pink (Ultimo.7 Multi Quat Sanitiser)
    '#e0f0f8',  # light blue (Ultimo.6 Glass & Stainless)
]


def set_random_colors(apps, schema_editor):
    Product = apps.get_model('chemsapp', 'Product')
    products = list(Product.objects.filter(wall_chart_color__isnull=True) |
                    Product.objects.filter(wall_chart_color=''))
    for product in products:
        product.wall_chart_color = random.choice(WALL_CHART_COLORS)
        product.save()


def clear_colors(apps, schema_editor):
    Product = apps.get_model('chemsapp', 'Product')
    Product.objects.filter(wall_chart_color__in=WALL_CHART_COLORS).update(wall_chart_color=None)


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0014_set_default_wall_chart_color'),
    ]

    operations = [
        migrations.RunPython(set_random_colors, clear_colors),
    ]
