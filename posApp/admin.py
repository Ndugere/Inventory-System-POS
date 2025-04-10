from django.contrib import admin
from posApp.models import Category, Products, Sales, salesItems, MeasurementType, Report

# Register your models here.

@admin.register(MeasurementType)
class MeasurementTypeAdmin(admin.ModelAdmin):
    model = MeasurementType
    fieldsets=[
        ("Measurement Info:", {"fields": ['name', 'short_name', 'type']})
    ]
    list_display = ['name', 'short_name', 'type']
    list_filter = ['type']
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    fieldsets = [
        ("Category Info: ", {"fields": ['name', 'description', 'measurement_type']})
    ]
    list_display = ['name', 'measurement_type']
    list_filter = ['name', 'measurement_type']
    
@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    model = Products
    fieldsets =[
        ("Product Info: ", {"fields": ['code', 'name', 'category_id', "measurement_value",'description', 'available_quantity', 'buy_price', 'min_sell_price', 'max_sell_price', 'status']})
    ]
    list_display = ['name', 'category_id', 'buy_price', 'min_sell_price', "max_sell_price",]
    list_filter = ['category_id', 'name', 'buy_price',  'min_sell_price', "max_sell_price",]

class SaleItemsAdmin(admin.TabularInline):
    model = salesItems
    
@admin.register(Sales)
class SalesAdmin(admin.ModelAdmin):
    model = Sales
    fieldsets = [
        
    ]
    inlines = [SaleItemsAdmin]
    
    list_display = []
    list_filter = []
    
    
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    model = Report
    fieldsets = [
        ("Report Info:", {"fields": ['name', 'generated_on', 'type']}),
        ("Details", {"fields": ['json']})
    ]
    readonly_fields = ["generated_on"]
    list_display = ['name', 'type', 'generated_on']
    list_filter = ['type']
# admin.site.register(Employees)
