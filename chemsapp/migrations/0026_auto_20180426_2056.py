# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-04-26 20:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0025_auto_20180413_0827'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='subCategory',
        ),
        migrations.AddField(
            model_name='product',
            name='subCategory',
            field=models.ManyToManyField(blank=True, null=True, related_name='subcategories', to='chemsapp.ProductCategory'),
        ),
    ]
