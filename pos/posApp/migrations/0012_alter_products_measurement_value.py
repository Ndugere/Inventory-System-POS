# Generated by Django 5.1.5 on 2025-01-20 13:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0011_alter_measurementtype_short_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='measurement_value',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='posApp.measurementtype'),
        ),
    ]
