import math  # Import the math module for rounding up
from django.db.models.signals import post_save, post_delete, pre_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum, F, Min, Max
from .models import Stocks, Products

"""
@ receiver(pre_save, sender=Stocks)
def update_product_before_save(sender, instance, **kwargs):
   
    product = instance.product_id 
    # Fetch remaining active stocks for the product
    stocks = Stocks.objects.filter(product_id=product, status=1)

    # Update product's buy_price and quantity
   
    
    print(f"{product.name} Stock Quantity: {instance.quantity}")
    product.quantity = product.quantity - instance.quantity  # quantity  
    if product.quantity < 0:
        product.quantity = 0
    
    print(f"{product.name} Quantity: {product.quantity}")  
    product.save()
"""    
@receiver(post_save, sender=Stocks)
def update_product_prices(sender, instance, **kwargs):
    """
    Update the buy_price and quantity of the associated product.
    """
    product = instance.product_id
    # Calculate the weighted average cost price
    stocks = Stocks.objects.filter(product_id=product, status=1)  # Only consider active stocks

    # Adjust total_cost calculation to use per-unit cost
    total_cost = stocks.aggregate(total_cost=Sum('cost_price'))['total_cost'] or 0

    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
   
    if total_quantity > 0:
        product.buy_price = total_cost / total_quantity  # Weighted average
        product.status = 1  # Set status to active if there are stocks
    else:
        product.buy_price = 0  # No active stocks, set to 0
        product.status = 0
        
    product.quantity = total_quantity  # Update total quantity
    
    product.save()
 
@receiver(post_delete, sender=Stocks)
def update_product_on_stock_delete(sender, instance, **kwargs):
    """
    #Update the associated product's quantity when a stock is deleted.
    """
    product = instance.product_id
    # Fetch remaining active stocks for the product
    stocks = Stocks.objects.filter(product_id=product, status=1)

    # Update product's buy_price and quantity
    total_cost = stocks.aggregate(total_cost=Sum('cost_price'))['total_cost'] or 0

    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
   
    if total_quantity > 0:
        product.buy_price = total_cost / total_quantity  # Weighted average
        product.status = 1  # Set status to active if there are stocks
    else:
        product.buy_price = 0  # No active stocks, set to 0
        product.status = 0
        
    
    product.quantity = total_quantity  # Update total quantity
    
    product.save()