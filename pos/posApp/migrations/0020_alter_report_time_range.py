# Generated by Django 5.1.5 on 2025-01-22 16:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0019_alter_report_time_range'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='time_range',
            field=models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('annual', 'Annual')], max_length=10, null=True, verbose_name='Time Range'),
        ),
    ]
