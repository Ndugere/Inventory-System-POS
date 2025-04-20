import math  # Import the math module for rounding up
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum, F, Min, Max, Avg
from .models import Stocks, Products

@receiver(post_save, sender=Stocks)
def update_product_prices(sender, instance, **kwargs):
    """
    Update the buy_price and quantity of the associated product when a stock is added or updated.
    """
    product = instance.product_id
    # Fetch relevant stocks
    stocks = Stocks.objects.filter(product_id=product, status=1)  # Only consider active stocks

    # Calculate the average unit price
    average_unit_price = stocks.aggregate(average_unit_price=Avg('unit_price'))['average_unit_price'] or 0
    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    product.buy_price = average_unit_price  # Set buy_price to the average unit price
    product.quantity = total_quantity  # Update total quantity
    product.status = 1 if total_quantity > 0 else 0  # Update status based on stock availability
    product.save()

@receiver(post_delete, sender=Stocks)
def update_product_on_stock_delete(sender, instance, **kwargs):
    """
    Update the associated product's quantity and buy_price when a stock is deleted.
    """
    product = instance.product_id
    # Fetch remaining relevant stocks
    stocks = Stocks.objects.filter(product_id=product, status=1)

    # Calculate the average unit price
    average_unit_price = stocks.aggregate(average_unit_price=Avg('unit_price'))['average_unit_price'] or 0
    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    product.buy_price = average_unit_price  # Set buy_price to the average unit price
    product.quantity = total_quantity  # Update total quantity
    product.status = 1 if total_quantity > 0 else 0  # Update status based on stock availability
    product.save()