# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-31 05:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chemsapp', '0008_product_uploadedby'),
    ]

    operations = [
        migrations.AddField(
            model_name='distributor',
            name='primaryImageLink',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='geocodingDetail',
            field=models.TextField(blank=True, max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='products',
            field=models.ManyToManyField(blank=True, null=True, related_name='customers', to='chemsapp.Product'),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='customers',
            field=models.ManyToManyField(blank=True, null=True, related_name='distributors', to='chemsapp.Customer'),
        ),
        migrations.AlterField(
            model_name='distributor',
            name='geocodingDetail',
            field=models.TextField(blank=True, max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='infoSheet',
            field=models.FileField(blank=True, null=True, upload_to='documents/'),
        ),
        migrations.AlterField(
            model_name='product',
            name='safetyWears',
            field=models.ManyToManyField(blank=True, related_name='products', to='chemsapp.SafetyWear'),
        ),
        migrations.AlterField(
            model_name='product',
            name='sdsSheet',
            field=models.FileField(blank=True, null=True, upload_to='documents/'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profileType',
            field=models.CharField(blank=True, choices=[('customer', 'customer'), ('distributor', 'distributor'), ('admin', 'admin')], default='customer', max_length=255, null=True),
        ),
    ]
