# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-27 00:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0027_productcategory_issubcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='size',
            name='isBag',
            field=models.BooleanField(default=False),
        ),
    ]
