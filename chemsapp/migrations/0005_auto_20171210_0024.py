# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-10 00:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0004_product_geocodingdetail'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='geocodingDetail',
            field=models.TextField(max_length=1500, null=True),
        ),
    ]
