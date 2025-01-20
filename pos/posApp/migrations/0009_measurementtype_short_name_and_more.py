# Generated by Django 5.1.5 on 2025-01-20 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0008_alter_category_measurement_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='measurementtype',
            name='short_name',
            field=models.CharField(default='L', max_length=1, verbose_name='Short Name'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='measurement_type',
            field=models.CharField(blank=True, choices=[('size', 'Size'), ('length', 'Length'), ('volume', 'Volume'), ('weight', 'Weight')], max_length=10, verbose_name='Measurement'),
        ),
        migrations.AlterField(
            model_name='measurementtype',
            name='type',
            field=models.CharField(choices=[('size', 'Size'), ('length', 'Length'), ('volume', 'Volume'), ('weight', 'Weight')], default='size', max_length=10, verbose_name='Measurement Type'),
        ),
    ]
