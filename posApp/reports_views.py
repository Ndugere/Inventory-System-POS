from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour
from datetime import datetime, timedelta
from posApp.models import Sales, salesItems, Products  # Adjust imports as needed
import json
from decimal import Decimal

@login_required
def reports_data(request):
    """
    Returns chart data filtered by a single date or a date range.
    Expected GET parameters:
      - report_date (for single day)
      - OR start_date and end_date (for date range)
    """
    if 'report_date' in request.GET:
        report_date = request.GET.get('report_date')
        sales = Sales.objects.filter(date_added__date=report_date)

    elif 'start_date' in request.GET and 'end_date' in request.GET:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        sales = Sales.objects.filter(date_added__date__range=[start_date, end_date])

    else:
        today = datetime.today().date()
        sales = Sales.objects.filter(date_added__date=today)
        hourly_sales = sales.annotate(hour=ExtractHour('date_added')).values('hour').annotate(
            hourly_total=Sum('grand_total'),
            hourly_cost=Sum(F('salesitems__product_id__buy_price') * F('salesitems__qty')),
            hourly_profit=Sum('grand_total') - Sum(F('salesitems__product_id__buy_price') * F('salesitems__qty'))
        ).order_by('hour')

        sales_trend = {
            "hours": [data['hour'] for data in hourly_sales],
            "amounts": [data['hourly_total'] for data in hourly_sales],
            "costs": [data['hourly_cost'] for data in hourly_sales],
            "profits": [data['hourly_profit'] for data in hourly_sales],
        }

        # Day's Revenue
        revenue = sales.aggregate(
            cash=Sum(Case(When(payment_method='cash', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method='mpesa', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            revenue=Sum('grand_total')
        )

    # Top Selling Products
    top_selling = salesItems.objects.filter(sale_id__date_added__date=today).values(
        "product_id__description", "product_id__name"
    ).annotate(total_sold=Sum("qty")).order_by("-total_sold")[:10]
    top_selling_data = {
        "products": [f"{item['product_id__name']} ({item['product_id__description']})" for item in top_selling],
        "quantities": [item["total_sold"] for item in top_selling]
    }

    # Stock Levels
    stock_levels = Products.objects.values("code", "name", "description").annotate(stock=Sum("available_quantity")).order_by("stock")[:5]
    stock_levels_data = {
        "products": [f"{item['name']} ({item['description']})" for item in stock_levels],
        "quantities": [item["stock"] for item in stock_levels]
    }

    # Convert Decimal to float for JSON serialization
    revenue = {k: float(v) if isinstance(v, Decimal) else v for k, v in revenue.items()}

    data = {
        "sales_trend": sales_trend,
        "revenue_breakdown": revenue, 
        "top_selling": top_selling_data,
        "stock_levels": stock_levels_data
    }
    return JsonResponse(data, safe=False)

@login_required
def reports_detail_data(request):
    """
    Returns detailed report data for a given chart.
    Expected GET parameters:
      - chart: the type of chart (e.g., "sales")
      - id: an identifier (for sales, the date string)
    """
    chart_type = request.GET.get('chart')
    identifier = request.GET.get('id')

    pass
