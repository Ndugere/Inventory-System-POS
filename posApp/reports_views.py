from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour, TruncDate
from django.db.models import ExpressionWrapper
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
    # Define a cost expression that multiplies buy price and quantity.
    cost_expression = ExpressionWrapper(
        F('salesitems__product_id__buy_price') * F('salesitems__qty'),
        output_field=FloatField()
    )

    def day_report(date):        
        # Sales trend
        sales = Sales.objects.filter(date_added__date=date)
        hourly_sales = sales.annotate(hour=ExtractHour('date_added')
            ).values('hour').annotate(
            # Using distinct=True for grand_total avoids double-counting when a sale has multiple items.
            hourly_total=Sum('grand_total', distinct=True),
            hourly_cost=Sum(cost_expression),
            hourly_profit=Sum('grand_total', distinct=True) - Sum(cost_expression)
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
        top_selling = salesItems.objects.filter(sale_id__date_added__date=date).values(
            "product_id__description", "product_id__name"
        ).annotate(total_sold=Sum("qty")).order_by("-total_sold")[:10]
        top_selling_data = {
            "products": [f"{item['product_id__name']} ({item['product_id__description']})" for item in top_selling],
            "quantities": [item["total_sold"] for item in top_selling]
        }
        
        return {"sales_trend": sales_trend, "revenue": revenue, "top_selling": top_selling_data}

    if 'report_date' in request.GET:
        report_date = request.GET.get('report_date')
        report = day_report(report_date)
        sales_trend = report["sales_trend"]
        revenue = report["revenue"]
        top_selling_data = report["top_selling"]
       
    
    elif 'start_date' in request.GET and 'end_date' in request.GET:
        # Convert start_date and end_date strings to date objects.
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Expected YYYY-MM-DD."}, status=400)

        sales = Sales.objects.filter(date_added__date__range=[start_date, end_date])

        # Group by date using TruncDate
        date_sales = sales.annotate(date=TruncDate('date_added')).values('date').annotate(
            # Use distinct=True to avoid double-counting grand_total when joining with salesItems
            date_total=Sum('grand_total', distinct=True),
            date_cost=Sum(cost_expression),
            date_profit=Sum('grand_total', distinct=True) - Sum(cost_expression)
        ).order_by('date')

        sales_trend = {
            "dates": [data['date'] for data in date_sales],
            "amounts": [data['date_total'] for data in date_sales],
            "costs": [data['date_cost'] for data in date_sales],
            "profits": [data['date_profit'] for data in date_sales],
        }

        # Revenue breakdown remains the same.
        revenue = sales.aggregate(
            cash=Sum(Case(When(payment_method='cash', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method='mpesa', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            revenue=Sum('grand_total')
        )

        # Top Selling Products using the same date range.
        top_selling = salesItems.objects.filter(
            sale_id__date_added__date__range=[start_date, end_date]
        ).values(
            "product_id__description", "product_id__name"
        ).annotate(total_sold=Sum("qty")).order_by("-total_sold")[:10]

        top_selling_data = {
            "products": [f"{item['product_id__name']} ({item['product_id__description']})" for item in top_selling],
            "quantities": [item["total_sold"] for item in top_selling]
        }

    else:
        today = datetime.today().date()
        report = day_report(today)
        sales_trend = report["sales_trend"]
        revenue = report["revenue"]
        top_selling_data = report["top_selling"]

    # Stock Levels
    stock_levels = Products.objects.values("code", "name", "description").annotate(
        stock=Sum("available_quantity")
    ).order_by("stock")[:5]
    stock_levels_data = {
        "products": [f"{item['name']} ({item['description']})" for item in stock_levels],
        "quantities": [item["stock"] for item in stock_levels]
    }

    # Convert Decimal to float for JSON serialization, using 0 as a fallback for None.
    revenue = {k: float(v) if v is not None else 0 for k, v in revenue.items()}

    data = {
        "sales_trend": sales_trend,
        "revenue_breakdown": revenue, 
        "top_selling": top_selling_data,
        "stock_levels": stock_levels_data
    }
    return JsonResponse(data, safe=False)
