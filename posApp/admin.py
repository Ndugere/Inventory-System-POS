from django.contrib import admin
from posApp.models import Category, Products, Sales, salesItems, Report

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    model = Category
    fieldsets = [
        ("Category Info: ", {"fields": ['name']})
    ]
    list_display = ['name']
    list_filter = ['name']
    
@admin.register(Products)
class ProductAdmin(admin.ModelAdmin):
    model = Products
    fieldsets =[
        ("Product Info: ", {"fields": ['code', 'name', 'category_id', "volume_type", "measurement_value", 'available_quantity', 'buy_price', 'min_sell_price', 'max_sell_price', 'status']})
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
