from datetime import datetime, timedelta
from unicodedata import category
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Category(models.Model):
    name = models.CharField("Category Name", max_length=100, blank=False)
    status = models.IntegerField("Status", default=1) 
    date_added = models.DateTimeField(default=timezone.now) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return str.capitalize(self.name)
    
    class Meta:    
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['name']

class Products(models.Model):
    class VolumeType(models.TextChoices):
        MILLIGRAMS = 'mg', _('Milligrams')
        GRAMS = 'g', _('Grams')
        MILLILITERS = "ml", _("Milliliters")
        LITERS = "L", _("Liters")
        PACKS = "packs", _("Packs")
        
    code = models.CharField("Product Code", max_length=100, unique=True, blank=False)
    category_id = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField("Product Name", max_length=100, blank=False)
    volume_type = models.CharField("Volume Type", max_length=100, choices=VolumeType.choices, default=VolumeType.MILLILITERS, blank=False)
    measurement_value = models.PositiveIntegerField("Measurement Value", default=0)
    quantity = models.PositiveIntegerField("Quantity", default=0)
    min_sell_price = models.FloatField("Minimum Sell Price", default=0)
    max_sell_price = models.FloatField("Maximum Sell Price", default=0)
    buy_price = models.FloatField("Buy Price", default=0)
    status = models.IntegerField("Status", default=0)
    
    def get_volume(self):
        return f"{self.measurement_value}{self.volume_type}"

    def __str__(self):
        return f"{str.capitalize(self.name)} ({self.measurement_value}{self.volume_type})"
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        unique_together = (("name", "measurement_value", "volume_type"))
        ordering = ["code", "name"]

class Supplier(models.Model):
    name = models.CharField("Supplier Name", max_length=100, blank=False)
    phone_number = models.CharField("Phone Number", max_length=15, blank=True, null=True)
    email = models.EmailField("Email", blank=True, null=True)
    address = models.TextField("Address", blank=True, null=True)
    status = models.IntegerField(default=1) 
    date_added = models.DateTimeField(auto_now_add=True) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return str.capitalize(self.name)
    
    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        ordering = ['name']

class Stocks(models.Model):
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)
    supplier_id = models.ForeignKey(Supplier, on_delete=models.RESTRICT, null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.FloatField(default=0)
    cost_price = models.FloatField(default=0)
    status = models.IntegerField(default=1)
    delivery_date = models.DateTimeField(auto_now_add=True) 
    date_updated = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"{self.product_id.name} - {self.batch_number}"
    
    def update_status(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            self.status = 0
            self.save()
        else:
            self.status = 1
            self.save()
            
    def is_expired(self):
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return True
        return False
    
    def is_expiring_soon(self):
        if self.expiry_date and (self.expiry_date - timezone.now().date()).days <= 7:
            return True
        return False
    def is_new(self):
        now = timezone.now()
        if now - self.delivery_date < timedelta(days=7):
            return True
        return False
    
    class Meta:
        verbose_name = "Stock"
        verbose_name_plural = "Stocks"
        ordering = ['-delivery_date', '-date_updated']

class Sales(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", _("Cash")
        MPESA = "mpesa", _("M-Pesa")

    code = models.CharField(max_length=100)
    sub_total = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    grand_total = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    tax = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    tendered_amount = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    amount_change = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    payment_method = models.CharField(  # New field
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    mpesa_transaction_code = models.CharField(max_length=20, blank=True)
    served_by = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="served_by")
    date_added = models.DateTimeField(auto_now_add=True) 
    date_updated = models.DateTimeField(auto_now=True) 

    def save(self, *args, **kwargs):
        if self.mpesa_transaction_code:
            self.mpesa_transaction_code = self.mpesa_transaction_code.upper()
        super(Sales, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.payment_method}"
    
    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-date_added', '-date_updated']

class salesItems(models.Model):
    sale_id = models.ForeignKey(Sales, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)
    stock_id = models.ForeignKey(Stocks, on_delete=models.CASCADE)
    price = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    qty = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    total = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
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

