from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour
from django.db.models import ExpressionWrapper
from datetime import datetime, timedelta
from models import Sales, salesItems, Products  # Adjust imports as needed
from collections import Counter
from decimal import Decimal

@login_required
def reports_data(request):
    """
    Returns chart data filtered by a single date or a date range.
    Expected GET parameters:
      - report_date (for single day)
      - OR start_date and end_date (for date range)
    """
    # Define cost expression to compute cost as buy_price * quantity.
    cost_expression = ExpressionWrapper(
        F('salesitems__product_id__buy_price') * F('salesitems__qty'),
        output_field=FloatField()
    )

    def day_report(date_value):
        # Sales trend: group sales by hour.
        sales = Sales.objects.filter(date_added__date=date_value)
        hourly_sales = sales.annotate(hour=ExtractHour('date_added')
            ).values('hour').annotate(
            hourly_total=Sum('grand_total', distinct=True),
            hourly_cost=Sum(cost_expression),
            hourly_profit=Sum('grand_total', distinct=True) - Sum(cost_expression)
        ).order_by('hour')

        sales_trend = {
            "hours": [record['hour'] for record in hourly_sales],
            "amounts": [record['hourly_total'] for record in hourly_sales],
            "costs": [record['hourly_cost'] for record in hourly_sales],
            "profits": [record['hourly_profit'] for record in hourly_sales],
        }

        # Revenue breakdown by payment method.
        revenue = sales.aggregate(
            cash=Sum(Case(When(payment_method='cash', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method='mpesa', then=F('grand_total')), default=Value(0), output_field=FloatField())),
            revenue=Sum('grand_total')
        )

        # Top selling products for the day.
        top_selling = salesItems.objects.filter(sale_id__date_added__date=date_value).values(
            "product_id__description", "product_id__name"
        ).annotate(total_sold=Sum("qty")).order_by("-total_sold")[:10]
        top_selling_data = {
            "products": [f"{item['product_id__name']} ({item['product_id__description']})" for item in top_selling],
            "quantities": [item["total_sold"] for item in top_selling]
        }
        return {"sales_trend": sales_trend, "revenue": revenue, "top_selling": top_selling_data}

    # Determine the date(s) for which to generate the report.
    if 'report_date' in request.GET:
        report_date = request.GET.get('report_date')
        # Ensure proper date conversion if needed.
        try:
            report_date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid report_date format. Expected YYYY-MM-DD."}, status=400)
        report = day_report(report_date_obj)
        sales_trend = report["sales_trend"]
        revenue = report["revenue"]
        top_selling_data = report["top_selling"]

    elif 'start_date' in request.GET and 'end_date' in request.GET:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Expected YYYY-MM-DD."}, status=400)

        # Build a list of dates in the range.
        current_date = start_date
        date_reports = {}
        while current_date <= end_date:
            date_reports[current_date.strftime('%Y-%m-%d')] = day_report(current_date)
            current_date += timedelta(days=1)

        # Aggregate daily results.
        sales_trend = {"dates": [], "amounts": [], "costs": [], "profits": []}
        revenue = {"cash": 0, "mpesa": 0, "revenue": 0}
        top_counter = Counter()

        for date_str, data in date_reports.items():
            sales_trend["dates"].append(date_str)
            daily_trend = data["sales_trend"]
            sales_trend["amounts"].append(sum(daily_trend["amounts"]))
            sales_trend["costs"].append(sum(daily_trend["costs"]))
            sales_trend["profits"].append(sum(daily_trend["profits"]))

            daily_revenue = data["revenue"]
            revenue["cash"] += daily_revenue.get("cash") or 0
            revenue["mpesa"] += daily_revenue.get("mpesa") or 0
            revenue["revenue"] += daily_revenue.get("revenue") or 0

            # Update the counter for top-selling products.
            daily_top = data["top_selling"]
            for product, qty in zip(daily_top["products"], daily_top["quantities"]):
                top_counter[product] += qty

        sorted_top = top_counter.most_common(10)
        top_selling_data = {
            "products": [item[0] for item in sorted_top],
            "quantities": [item[1] for item in sorted_top]
        }

    else:
        # Default to today's date.
        today = datetime.today().date()
        report = day_report(today)
        sales_trend = report["sales_trend"]
        revenue = report["revenue"]
        top_selling_data = report["top_selling"]

    # Stock Levels: fetch products with the lowest available_quantity.
    stock_levels = Products.objects.values("code", "name", "description").annotate(
        stock=Sum("available_quantity")
    ).order_by("stock")[:5]
    stock_levels_data = {
        "products": [f"{item['name']} ({item['description']})" for item in stock_levels],
        "quantities": [item["stock"] for item in stock_levels]
    }

    # Convert Decimal values to float for JSON serialization.
    revenue = {k: float(v) if v is not None else 0 for k, v in revenue.items()}

    data = {
        "sales_trend": sales_trend,
        "revenue_breakdown": revenue, 
        "top_selling": top_selling_data,
        "stock_levels": stock_levels_data
    }
    return JsonResponse(data, safe=False)
