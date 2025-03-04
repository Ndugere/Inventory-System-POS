# Generated by Django 5.1.5 on 2025-02-12 18:58

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posApp', '0006_alter_products_code'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MeasurementType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Measurement Name')),
                ('short_name', models.CharField(max_length=5, verbose_name='Short Name')),
                ('type', models.CharField(choices=[('size', 'Size'), ('length', 'Length'), ('volume', 'Volume'), ('weight', 'Weight')], default='size', max_length=10, verbose_name='Measurement Type')),
            ],
            options={
                'verbose_name': 'Measurement Type',
                'verbose_name_plural': 'Measurement Type',
            },
        ),
        migrations.CreateModel(
            name='MpesaPaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(editable=False, max_length=255)),
                ('customer_name', models.CharField(max_length=255)),
                ('phone_number', models.CharField(max_length=15)),
                ('amount_received', models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True)),
                ('account_reference', models.CharField(max_length=255)),
                ('transaction_desc', models.CharField(max_length=255)),
                ('result_code', models.IntegerField(blank=True, null=True)),
                ('result_desc', models.CharField(blank=True, max_length=255, null=True)),
                ('transaction_time', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('completed', 'Completed'), ('cancelled', 'Cancelled'), ('pending', 'Pending')], default='pending', max_length=50)),
                ('mpesa_response', models.JSONField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Grocery', max_length=100, verbose_name='Store Name')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Store',
                'verbose_name_plural': 'Stores',
            },
        ),
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ['name'], 'verbose_name': 'Category', 'verbose_name_plural': 'Categories'},
        ),
        migrations.AlterModelOptions(
            name='products',
            options={'ordering': ['code', 'name'], 'verbose_name': 'Product', 'verbose_name_plural': 'Products'},
        ),
        migrations.AlterModelOptions(
            name='sales',
            options={'ordering': ['-date_added', '-date_updated'], 'verbose_name': 'Sale', 'verbose_name_plural': 'Sales'},
        ),
        migrations.AddField(
            model_name='category',
            name='measurement_type',
            field=models.CharField(blank=True, choices=[('size', 'Size'), ('length', 'Length'), ('volume', 'Volume'), ('weight', 'Weight')], max_length=10, verbose_name='Measurement'),
        ),
        migrations.AddField(
            model_name='products',
            name='buy_price',
            field=models.FloatField(default=0, verbose_name='Buy Price'),
        ),
        migrations.AddField(
            model_name='products',
            name='max_sell_price',
            field=models.FloatField(default=0, verbose_name='Max Sell Price'),
        ),
        migrations.AddField(
            model_name='products',
            name='min_sell_price',
            field=models.FloatField(default=0, verbose_name='Min Sell Price'),
        ),
        migrations.AddField(
            model_name='sales',
            name='payment_method',
            field=models.CharField(choices=[('cash', 'Cash'), ('mpesa', 'M-Pesa')], default='cash', max_length=10),
        ),
        migrations.AddField(
            model_name='sales',
            name='served_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, related_name='served_by', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Category Name'),
        ),
        migrations.AlterField(
            model_name='category',
            name='status',
            field=models.IntegerField(default=1, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='products',
            name='code',
            field=models.CharField(max_length=100, unique=True, verbose_name='Product Code'),
        ),
        migrations.AlterField(
            model_name='products',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='products',
            name='description',
            field=models.TextField(verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='products',
            name='name',
            field=models.CharField(max_length=100, verbose_name='Product Name'),
        ),
        migrations.AlterField(
            model_name='products',
            name='status',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='sales',
            name='date_added',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='products',
            name='measurement_value',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='posApp.measurementtype'),
        ),
        migrations.AlterUniqueTogether(
            name='products',
            unique_together={('name', 'measurement_value', 'description')},
        ),
        migrations.CreateModel(
            name='StockMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('movement_type', models.CharField(choices=[('addition', 'Addition'), ('subtraction', 'Subtraction')], max_length=20)),
                ('quantity', models.FloatField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posApp.products')),
            ],
            options={
                'verbose_name': 'Stock Movement',
                'verbose_name_plural': 'Stock Movements',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Branch Name')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posApp.store')),
            ],
            options={
                'verbose_name': 'Store Branches',
                'verbose_name_plural': 'Stores Branches',
            },
        ),
        migrations.RemoveField(
            model_name='products',
            name='price',
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Title')),
                ('generated_on', models.DateTimeField(auto_now_add=True)),
                ('type', models.CharField(choices=[('inventory', 'Inventory Report'), ('sales', 'Sales Report')], default='inventory', max_length=10, verbose_name='Report Type')),
                ('time_range', models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('annual', 'Annual')], max_length=10, null=True, verbose_name='Time Range')),
                ('json', models.TextField(verbose_name='Report Data')),
                ('generated_by', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='report_generated_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Report',
                'verbose_name_plural': 'Reports',
                'ordering': ['-generated_on'],
                'unique_together': {('name', 'generated_on')},
            },
        ),
    ]
