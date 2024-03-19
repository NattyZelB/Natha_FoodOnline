# Generated by Django 4.2.2 on 2023-08-28 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0005_alter_openinghour_from_hour_and_more'),
        ('orders', '0003_alter_payment_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='total_data',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='vendors',
            field=models.ManyToManyField(blank=True, to='vendor.vendor'),
        ),
    ]
