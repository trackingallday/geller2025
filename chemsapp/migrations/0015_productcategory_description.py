# -*- coding: utf-8 -*-
from django.db import migrations, models
from datetime import datetime  # Changed from django.utils.datetime_safe


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0014_auto_20180305_2110'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='description',
            field=models.TextField(default=datetime.now, max_length=1000),  # Removed datetime_safe
            preserve_default=False,
        ),
    ]