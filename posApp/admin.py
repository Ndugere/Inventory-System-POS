from django.contrib import admin
from posApp.models import Category, Products, Sales, salesItems, Report, Supplier, Stocks

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
        ("Product Info: ", {"fields": ['code', 'name', 'category_id', "measurement_type", "measurement_unit", "measurement_value"]})
    ]
    list_display = ['name', 'category_id', "measurement_type", ]
    list_filter = ['category_id', 'name', "measurement_type", ]
    search_fields = ['name', 'category_id__name']
    ordering = ['name']
    list_per_page = 10
    list_select_related = True

@admin.register(Supplier)
class Supplieradmin(admin.ModelAdmin):
    model = Supplier
    fieldsets = (
        ("Supplier Info", {
            "fields": (
                ('name', 'phone_number'),
                ('email', 'address'),
            ),
        }),
    )
    list_display = ['name', 'phone_number', 'email']
    list_filter = ['name', 'phone_number', 'email']
    search_fields = ['name', 'phone_number', 'email']
    ordering = ['name']
    list_per_page = 10
    list_select_related = True

@admin.register(Stocks)
class StocksAdmin(admin.ModelAdmin):
    model = Stocks
    fieldsets = [
        ("Stocks Info: ", {"fields": ['product_id__name', 'batch_number','quantity', 'cost_price']})
    ]
    list_display = ['product_id', 'batch_number', 'quantity']
    list_filter = ['product_id']
    search_fields = ['product_id__name']
    ordering = ['product_id']
    list_per_page = 10
    list_select_related = True
    

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
