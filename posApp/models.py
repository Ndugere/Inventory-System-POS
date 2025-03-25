from datetime import datetime, timedelta
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
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{str.casefold(self.name)}"
    
    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"

class Branch(models.Model):
    name = models.CharField("Branch Name", max_length=255, blank=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{str.casefold(self.name)}"
    
    class Meta:
        verbose_name = "Store Branches"
        verbose_name_plural = "Stores Branches"

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
        verbose_name = "Measurement Type"
        verbose_name_plural = "Measurement Type"
        
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
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

class Products(models.Model):
    code = models.CharField("Product Code", max_length=100, unique=True, blank=False)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField("Product Name", max_length=100, blank=False)
    description = models.TextField("Description")
    measurement_value = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True)
    buy_price = models.FloatField("Buy Price", default=0)
    min_sell_price = models.FloatField("Min Sell Price", default=0)    
    max_sell_price = models.FloatField("Max Sell Price", default=0)
    available_quantity = models.IntegerField(default=0)
    status = models.IntegerField(default=0) 
    date_added = models.DateTimeField(auto_now_add=True) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return self.code + " - " + self.name + " (" + self.description +")"
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = (("name", "measurement_value", "description"))
        ordering = ["code", "name"]

class Sales(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Cash")
        MPESA = "mpesa", _("M-Pesa")

    code = models.CharField(max_length=100)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    tendered_amount = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)
    payment_method = models.CharField(  # New field
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    served_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="served_by")
    date_added = models.DateTimeField(auto_now_add=True) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"{self.code} - {self.payment_method}"
    
    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-date_added', '-date_updated']

class salesItems(models.Model):
    sale_id = models.ForeignKey(Sales, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)
    price = models.FloatField(default=0)
    qty = models.FloatField(default=0)
    total = models.FloatField(default=0)
    
    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"

class Report(models.Model):
    class ReportType(models.TextChoices):
        INVENTORY = "inventory", _("Inventory Report")
        SALES = "sales", _("Sales Report")
    
    class ReportTimeRange(models.TextChoices):
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")
        ANNUAL = "annual", _("Annual")
    
    name = models.CharField("Title", max_length=100, blank=False)
    generated_on = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="report_generated_by")
    type = models.CharField("Report Type", choices=ReportType.choices, default=ReportType.INVENTORY, max_length=10)
    time_range = models.CharField("Time Range", choices=ReportTimeRange.choices, max_length=10, blank=True, null=True)
    json = models.TextField("Report Data", blank=False)
    
    def is_new(self):
        now = datetime.now().astimezone()
        if now - self.generated_on < timedelta(days=7):
            return True
    
    def __str__(self):
        return f"{str.upper(self.name)} -  {self.generated_on}"
    
    class Meta:
        verbose_name = "Report"
        verbose_name_plural = "Reports"
        unique_together = (("name", "generated_on"))
        ordering = ['-generated_on']

class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        ADDITION = 'addition', _('Addition')
        SUBTRACTION = 'subtraction', _('Subtraction')

    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} - {self.quantity}"

    class Meta:
        verbose_name = "Stock Movement"
        verbose_name_plural = "Stock Movements"
        ordering = ['-timestamp']

class MpesaPaymentTransaction(models.Model):
    class StatusChoices(models.TextChoices):
        COMPLETED = "completed", _("Completed")
        CANCELLED = "cancelled", _("Cancelled")
        PENDING = "pending", _("Pending")
        
    transaction_id = models.CharField(max_length=255, editable=False)
    customer_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    #amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)  # Amount received from M-Pesa
    account_reference = models.CharField(max_length=255)
    transaction_desc = models.CharField(max_length=255)
    result_code = models.IntegerField(null=True, blank=True)  # Store M-Pesa's result code (e.g., 0 for success)
    result_desc = models.CharField(max_length=255, null=True, blank=True)  # Description of the result
    transaction_time = models.DateTimeField(null=True, blank=True)  # The time the transaction was processed
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.PENDING)  # "Pending", "Success", "Failed"
    mpesa_response = models.JSONField(null=True, blank=True)  # Store the full response from M-Pesa\n    \n    # New field to distinguish payment types\n    transaction_method = models.CharField(\n        max_length=10, \n        choices=(\n            ('STK', 'STK'),\n            ('C2B', 'C2B'),\n            ('B2C', 'B2C'),\n            ('B2B', 'B2B')\n        ),\n        default='STK'\n    )\n    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)  # Link to a user if applicable\n    created_at = models.DateTimeField(auto_now_add=True)\n    updated_at = models.DateTimeField(auto_now=True)\n\n    def __str__(self):\n        return f\"Transaction {self.account_reference} - {self.status}\"\n        \n    class Meta:\n        verbose_name = \"Mpesa Payment\"\n        verbose_name_plural = \"Mpesa Payments\"\n        ordering = ['-transaction_time']\n```

