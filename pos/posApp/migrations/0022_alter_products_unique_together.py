# Generated by Django 5.1.5 on 2025-01-24 19:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0021_alter_products_status'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='products',
            unique_together={('name', 'measurement_value', 'description')},
        ),
    ]
