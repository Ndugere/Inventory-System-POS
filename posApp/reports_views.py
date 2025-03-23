from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour
from datetime import datetime, timedelta
from posApp.models import Sales, salesItems, Products  # Adjust imports as needed

@login_required
def reports_data(request):
    """
    Returns chart data filtered by a single date or a date range.
    Expected GET parameters:
      - report_date (for single day)
      - OR start_date and end_date (for date range)
    """
    report_date = request.GET.get('report_date')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    today = datetime.today().astimezone()

    if report_date:
        sales_trends = Sales.objects.filter(date_added__date=report_date)
        hourly_trends = sales_trends.annotate(
            hour=ExtractHour('date_added')
        ).values('hour').annotate(
            revenue=Sum('grand_total'),
            cost=Sum(F('salesitems__product_id__buy_price') * F('salesitems__qty')),
            profit=Sum(F('grand_total') - F('salesitems__product_id__buy_price') * F('salesitems__qty'))
        ).order_by('hour')
        
        sales_trends_data = {
            "hours": [data['hour'] for data in hourly_trends],
            "amounts": [data['revenue'] for data in hourly_trends],
            "costs": [data['cost'] for data in hourly_trends],
            "profits": [data['profit'] for data in hourly_trends],
        }
        date_revenue_breakdown = Sales.objects.filter(date_added__date=report_date).aggregate(
            cash=Sum(Case(When(payment_method="cash", then=F("grand_total")), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method="mpesa", then=F("grand_total")), default=Value(0), output_field=FloatField()))
        )
    elif start_date and end_date:
        sales_trends = Sales.objects.filter(date_added__date__range=[start_date, end_date])
        trends_data = sales_trends.annotate(
            date=F('date_added__date')
        ).values('date').annotate(
            revenue=Sum('grand_total'),
            cost=Sum(F('salesitems__product_id__buy_price') * F('salesitems__qty')),
            profit=Sum(F('grand_total') - F('salesitems__product_id__buy_price') * F('salesitems__qty'))
        ).order_by('date')
        
        sales_trends_data = {
            "dates": [str(data['date']) for data in trends_data],
            "amounts": [data['revenue'] for data in trends_data],
            "costs": [data['cost'] for data in trends_data],
            "profits": [data['profit'] for data in trends_data]
        }
        date_revenue_breakdown = Sales.objects.filter(date_added__date__range=[start_date, end_date]).aggregate(
            cash=Sum(Case(When(payment_method="cash", then=F("grand_total")), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method="mpesa", then=F("grand_total")), default=Value(0), output_field=FloatField()))
        )
    else:
        # Default: last 24 hours
        sales_trends = Sales.objects.filter(date_added__date=today - timedelta(hours=6))
        
        trend = sales_trends.annotate(hour=ExtractHour('date_added')).values('hour', 'grand_total').order_by('hour')
        for t in trend:
            print(f"Trend {t}")
          
        
        hourly_trends = sales_trends.annotate(
            hour=ExtractHour('date_added')
        ).values('hour').annotate(
            revenue=Sum('grand_total'),
            cost=Sum(F('salesitems__product_id__buy_price') * F('salesitems__qty')),
            profit=Sum(F('grand_total') - F('salesitems__product_id__buy_price') * F('salesitems__qty'))
        ).order_by('hour')
        
        sales_trends_data = {
            "hours": [data['hour'] for data in hourly_trends],
            "amounts": [data['revenue'] for data in hourly_trends],
            "costs": [data['cost'] for data in hourly_trends],
            "profits": [data['profit'] for data in hourly_trends],
        }
        date_revenue_breakdown = Sales.objects.filter(date_added__date=today).aggregate(
            cash=Sum(Case(When(payment_method="cash", then=F("grand_total")), default=Value(0), output_field=FloatField())),
            mpesa=Sum(Case(When(payment_method="mpesa", then=F("grand_total")), default=Value(0), output_field=FloatField()))
        )

    # Ensure total revenue matches the sum of cash and mpesa revenue
    total_revenue = date_revenue_breakdown["cash"] + date_revenue_breakdown["mpesa"]
    total_cost = sum(sales_trends_data["costs"])
    sales_revenue = sum(sales_trends_data["amounts"])
    total_profit = total_revenue - total_cost
    sales_profit = sales_revenue - sum(sales_trends_data["profits"])
    print(f"Total Revenue: {total_revenue}, Sales Revenue: {sales_revenue}, Total Cost: {total_cost}, Total Profit: {total_profit}, Sales Profit: {sales_profit}")

    # Revenue Breakdown
    revenue_breakdown = [date_revenue_breakdown["cash"] or 0, date_revenue_breakdown["mpesa"] or 0]

    # Top Selling Products
    top_selling = salesItems.objects.values("product_id__code").annotate(total_sold=Sum("qty")).order_by("-total_sold")[:10]
    top_selling_data = {
        "products": [item["product_id__code"] for item in top_selling],
        "quantities": [item["total_sold"] for item in top_selling]
    }

    # Stock Levels
    stock_levels = Products.objects.values("code").annotate(stock=Sum("available_quantity")).order_by("stock")
    stock_levels_data = {
        "products": [item["code"] for item in stock_levels],
        "quantities": [item["stock"] for item in stock_levels]
    }

    data = {
        "sales_trends": sales_trends_data,
        "revenue_breakdown": revenue_breakdown,
        "top_selling": top_selling_data,
        "stock_levels": stock_levels_data,
    }
    return JsonResponse(data)

@login_required
def reports_detail_data(request):
    """
    Returns detailed report data for a given chart element.
    Expected GET parameters:
      - chart: the type of chart (e.g., "sales")
      - id: an identifier (for sales, the date string)
    """
    chart_type = request.GET.get('chart')
    identifier = request.GET.get('id')

    if (chart_type == "sales" and identifier):
        # Return full sales details for the date provided
        details = Sales.objects.filter(date_added__date=identifier).values()
        return JsonResponse({"details": list(details)})

    return JsonResponse({"details": []})
