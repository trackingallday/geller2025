# Generated manually to sync Django's migration state with actual database
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chemsapp', '0004_migrate_distributor_to_standalone'),
    ]

    operations = [
        # This migration only updates Django's internal state to match the actual database
        # No database operations are performed because the table structure is already correct
        migrations.SeparateDatabaseAndState(
            state_operations=[
                # Tell Django about the Distributor model structure
                migrations.CreateModel(
                    name='Distributor',
                    fields=[
                        ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('phonenumber', models.CharField(default='', max_length=100)),
                        ('cellphonenumber', models.CharField(blank=True, max_length=100, null=True)),
                        ('businessname', models.CharField(default='', max_length=255)),
                        ('address', models.CharField(default='', max_length=500)),
                        ('profiletype', models.CharField(blank=True, choices=[('customer', 'customer'), ('distributor', 'distributor'), ('admin', 'admin')], default='distributor', max_length=255, null=True)),
                        ('hassetpassword', models.BooleanField(default=False)),
                        ('geocodingdetail', models.TextField(blank=True, max_length=1500, null=True)),
                        ('primaryimagelink', models.FileField(blank=True, null=True, upload_to='documents/')),
                        ('customers', models.ManyToManyField(blank=True, related_name='distributors', to='chemsapp.customer')),
                        ('users', models.ManyToManyField(blank=True, related_name='distributors', to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'abstract': False,
                    },
                ),
            ],
            # No database operations needed - table already exists with correct structure
            database_operations=[],
        ),
    ]
