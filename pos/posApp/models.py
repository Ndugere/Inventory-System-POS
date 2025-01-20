from datetime import datetime
from unicodedata import category
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Create your models here.

# class Employees(models.Model):
#     code = models.CharField(max_length=100,blank=True) 
#     firstname = models.TextField() 
#     middlename = models.TextField(blank=True,null= True) 
#     lastname = models.TextField() 
#     gender = models.TextField(blank=True,null= True) 
#     dob = models.DateField(blank=True,null= True) 
#     contact = models.TextField() 
#     address = models.TextField() 
#     email = models.TextField() 
#     department_id = models.ForeignKey(Department, on_delete=models.CASCADE) 
#     position_id = models.ForeignKey(Position, on_delete=models.CASCADE) 
#     date_hired = models.DateField() 
#     salary = models.FloatField(default=0) 
#     status = models.IntegerField() 
#     date_added = models.DateTimeField(default=timezone.now) 
#     date_updated = models.DateTimeField(auto_now=True) 

    # def __str__(self):
    #     return self.firstname + ' ' +self.middlename + ' '+self.lastname + ' '

class Store(models.Model):
    name = models.CharField("Store Name", max_length=100, blank=False, default="Grocery")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{str.casefold(self.name)}"
    
    class Meta:
        verbose_name="Store"
        verbose_name_plural ="Stores"

class Branch(models.Model):
    name = models.CharField("Branch Name", max_length=255, blank=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =  models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{str.casefold(self.name)}"
    
    class Meta:
        verbose_name="Store Branches"
        verbose_name_plural ="Stores Branches"

class MeasurementType(models.Model):
    class MEASUREMENT_CHOICES(models.TextChoices):
        SIZE = 'size', 'Size'
        LENGTH = 'length', 'Length'
        VOLUME = 'volume', 'Volume'
        WEIGHT = 'weight', 'Weight'
    
    name = models.CharField("Measurement Name", max_length=50)
    short_name = models.CharField("Short Name", max_length=5)
    type = models.CharField("Measurement Type", max_length=10, choices=MEASUREMENT_CHOICES.choices, default=MEASUREMENT_CHOICES.SIZE)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name="Measurement Type"
        verbose_name_plural ="Measurement Type"
        
class Category(models.Model):
    name = models.CharField("Category Name", max_length=100, blank=False)
    description = models.TextField("Description")
    measurement_type = models.CharField(_("Measurement"), choices=MeasurementType.MEASUREMENT_CHOICES.choices, max_length=10, blank=True)
    status = models.IntegerField("Status", default=1) 
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.name
    
    class Meta:    
        verbose_name="Category"
        verbose_name_plural="Categories"

class Products(models.Model):
    code = models.CharField("Product Code", max_length=100, unique=True, blank=False)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField("Product Name", max_length=100, blank=False)
    description = models.TextField("Description")
    measurement_value = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True)
    price = models.FloatField("Price", default=0)
    available_quantity = models.IntegerField(default=0)
    status = models.IntegerField(default=1) 
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.code + " - " + self.name
    
    class Meta:
        verbose_name="Product"
        verbose_name_plural = "Products"

class Sales(models.Model):
    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name="Sale"
        verbose_name_plural = "Sales"

class salesItems(models.Model):
    sale_id = models.ForeignKey(Sales,on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products,on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)
    
    class Meta:
        verbose_name="Sale Item"
        verbose_name_plural = "Sale Items"