# Generated by Django 4.2.2 on 2023-07-19 14:47

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_rename_plaatsnaam_userprofile_city_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='location',
            field=django.contrib.gis.db.models.fields.PointField(blank=True, null=True, srid=4326),
        ),
    ]
