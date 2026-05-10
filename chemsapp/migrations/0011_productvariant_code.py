from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0010_customercontact'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='code',
            field=models.CharField(max_length=255, unique=True, null=True, blank=True),
        ),
    ]
