# Generated by Django 4.2.2 on 2023-07-08 20:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(max_length=50)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, max_length=250)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.vendor')),
            ],
        ),
        migrations.CreateModel(
            name='FoodItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('food_title', models.CharField(max_length=50)),
                ('slug', models.SlugField(blank=True, max_length=100)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('image', models.ImageField(upload_to='foodimages')),
                ('is_available', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('catelgory', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='menu.category')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vendor.vendor')),
            ],
        ),
    ]
