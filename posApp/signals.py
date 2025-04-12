import math  # Import the math module for rounding up
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, F, Min, Max
from django.db.models.functions import Round
from .models import Stocks, Products
@receiver(post_save, sender=Stocks)
def update_product_prices(sender, instance, **kwargs):
    """
    #Update the buy_price and quantity of the associated product.
    """
    product = instance.product_id
    # Calculate the weighted average cost price
    stocks = Stocks.objects.filter(product_id=product, status=1)  # Only consider active stocks
    """
    # Adjust total_cost calculation to use per-unit cost
    total_cost = stocks.aggregate(
        total_cost=Sum(F('unit_price') * F('quantity'))
    )['total_cost'] or 0

    """
    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    """
    if total_quantity > 0:
        product.buy_price = total_cost / total_quantity  # Weighted average
        product.status = 1  # Set status to active if there are stocks
    else:
        product.buy_price = 0  # No active stocks, set to 0
        product.status = 0
    """
    product.quantity = total_quantity  # Update total quantity
    product.save()
    
@receiver(post_save, sender=Stocks)
def update_product_prices_based_on_stocks(sender, instance, **kwargs):
    
    #Update the min_sell_price and max_sell_price based on the lowest and highest cost_price of active stocks.
    
    product = instance.product_id
    stocks = Stocks.objects.filter(product_id=product, status=1)  # Only consider active stocks

    if stocks.exists():
        min_cost = stocks.aggregate(min_cost=Min('unit_price'))['min_cost']
        max_cost = stocks.aggregate(max_cost=Max('unit_price'))['max_cost']
        quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

        # Define markup percentages
        min_markup = 0.1  # 10% markup
        max_markup = 0.3  # 30% markup

        # Update sell prices per unit and round up to the nearest whole number
        product.min_sell_price = math.ceil(max_cost * (1 + min_markup))
        product.max_sell_price = math.ceil(max_cost * (1 + max_markup))
    else:
        # No active stocks, reset sell prices
        product.min_sell_price = 0
        product.max_sell_price = 0

    product.save()
    
@receiver(post_delete, sender=Stocks)
def update_product_on_stock_delete(sender, instance, **kwargs):
    """
    #Update the associated product's buy_price, quantity, and sell prices when a stock is deleted.
    """
    product = instance.product_id
    # Fetch remaining active stocks for the product
    stocks = Stocks.objects.filter(product_id=product, status=1)

    # Update product's buy_price and quantity
    total_cost = stocks.aggregate(
        total_cost=Sum(F('unit_price') * F('quantity'))
    )['total_cost'] or 0

    total_quantity = stocks.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    if total_quantity > 0:
        product.buy_price = total_cost / total_quantity  # Weighted average
        product.status = 1  # Set status to active if there are stocks
    else:
        product.buy_price = 0  # No active stocks, set to 0
        product.status = 0

    product.quantity = total_quantity  # Update total quantity

    # Update min_sell_price and max_sell_price
    if stocks.exists():
        min_cost = stocks.aggregate(min_cost=Min('unit_price'))['min_cost']
        max_cost = stocks.aggregate(max_cost=Max('unit_price'))['max_cost']

        # Define markup percentages
        min_markup = 0.1  # 10% markup
        max_markup = 0.3  # 30% markup

        # Update sell prices per unit
        product.min_sell_price = round(max_cost * (1 + min_markup), 2)
        product.max_sell_price = round(max_cost * (1 + max_markup), 2)
    else:
        # No active stocks, reset sell prices
        product.min_sell_price = 0
        product.max_sell_price = 0

    product.save()