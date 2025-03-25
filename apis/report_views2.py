from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour, TruncDate
from django.db.models import ExpressionWrapper
from datetime import datetime, timedelta
from models import Sales, salesItems, Products  # Adjust imports as needed
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

        date_list = {}
        keys_list = []
        while start_date <= end_date:
            keys_list.append(f"{start_date.strftime('%Y-%m-%d')}")
            day_data = day_report(start_date)
            date_list[f"{start_date.strftime('%Y-%m-%d')}"] = day_data
            start_date += timedelta(days=1)
            
        sales_trend={
            "dates": [],
            "amounts": [],
            "costs": [],
            "profits": [],
        }
        revenue = {
            "cash": 0,
            "mpesa": 0,
            "revenue": 0
        }
        aggregated_top_selling_data = {}
        
        for key in keys_list:
            sales_trend["dates"].append(key)
            
            #print(f"{'amounts'}: {sum(date_list[key]['sales_trend']['amounts'])}")
            sales_trend["amounts"].append(sum(date_list[key]['sales_trend']['amounts']))
            
            #print(f"{'costs'}: {sum(date_list[key]['sales_trend']['costs'])}")
            sales_trend["costs"].append(sum(date_list[key]['sales_trend']['costs']))
            
            #print(f"{'profits'}: {sum(date_list[key]['sales_trend']['profits'])}")
            sales_trend["profits"].append(sum(date_list[key]['sales_trend']['profits']))
            
            #print(f"{"revenue"}: {date_list[key]['revenue']}\n")
            revenue["cash"] += date_list[key]['revenue']['cash'] or 0
            revenue['mpesa'] += date_list[key]['revenue']['mpesa'] or 0
            revenue['revenue'] += date_list[key]['revenue']['revenue'] or 0
            
            # Aggregate top selling data
            day_top = date_list[key]['top_selling']
            for product, qty in zip(day_top['products'], day_top['quantities']):
                aggregated_top_selling_data[product] = aggregated_top_selling_data.get(product, 0) + qty
        
        sorted_top = sorted(aggregated_top_selling_data.items(), key=lambda x: x[1], reverse=True)[:10]
        top_selling_data = {
            "products": [item[0] for item in sorted_top],
            "quantities": [item[1] for item in sorted_top]
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
