# Generated by Django 5.1.5 on 2025-01-25 05:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0023_sales_served_by'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='generated_by',
            field=models.ForeignKey(default=3, on_delete=django.db.models.deletion.RESTRICT, related_name='report_generated_by', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
