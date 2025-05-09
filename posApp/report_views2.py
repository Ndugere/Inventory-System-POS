from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Case, When, F, Value, FloatField
from django.db.models.functions import ExtractHour, Coalesce
from django.db.models import ExpressionWrapper
from datetime import datetime, timedelta
from posApp.models import Sales, salesItems, Products, Supplier, Stocks, Category
from collections import Counter
from decimal import Decimal
import json
from django.utils import timezone

@login_required
def home(request):
        context = {}        
        return render(request, "posApp/home-alt.html", context)
        return redirect("pos-page")

@login_required
def inventory(request):
    stocks = Stocks.objects.all()
    context = {
        "stocks": stocks
    }
    return render(request, "posApp/inventory/inventory.html", context)

@login_required
def inventory_data(request):
    """
    Returns inventory data for the products.
    """
    data_type = request.GET.get('type', '')

    if data_type == 'expiring_soon':
        stocks = Stocks.objects.filter(expiry_date__lte=timezone.now().date() + timedelta(days=7), status=1)[:5]
        data = {
            "products": [f"{stock.product_id.name}" for stock in stocks],
            "quantities": [stock.quantity for stock in stocks]
        }
    elif data_type == 'low_stock':
        products = Products.objects.filter(quantity__lte=10).order_by('quantity')[:5]
        data = {
            "products": [f"{product.name}({product.get_volume()})" for product in products],
            "quantities": [product.quantity for product in products]
        }
    elif data_type == 'top_selling':
        top_selling = salesItems.objects.values(
            "product_id__name", "product_id__measurement_value", "product_id__volume_type"
        ).annotate(total_sold=Sum("qty")).order_by("-total_sold")[:5]
        data = {
            "products": [f'{item["product_id__name"]} ({item["product_id__measurement_value"]}{item["product_id__volume_type"]})' for item in top_selling],
            "quantities": [item["total_sold"] for item in top_selling]
        }
    elif data_type == 'stock_value':
        categories = Category.objects.all()
        data = {
            "categories": [category.name for category in categories],
            "values": [
                Stocks.objects.filter(product_id__category_id=category).aggregate(
                    total_value=Sum(
                        Case(
                            When(quantity__gt=0, then=(F('unit_price')* F('quantity'))),
                            default=Value(0.0, output_field=FloatField()),
                            output_field=FloatField()
                        )
                        , output_field=FloatField()
                    )
                )['total_value'] or 0 for category in categories
            ]
        }
    elif data_type == 'most_profitable':
        products = Products.objects.annotate(
            max_profit=(F('max_sell_price') - F('buy_price')),
            min_profit=(F('min_sell_price') - F('buy_price'))
        ).order_by('-max_profit')[:3]
        data = {
            "products": [f"{product.name} ({product.measurement_value}{product.volume_type})" for product in products],
            "cost_prices": [product.buy_price for product in products],
            "max_profits": [product.max_profit for product in products],
            "min_profits": [product.min_profit for product in products]
        }
    elif data_type == 'least_profitable':
        products = Products.objects.annotate(
            max_profit=(F('max_sell_price') - F('buy_price')),
            min_profit=(F('min_sell_price') - F('buy_price'))
        ).order_by('max_profit')[:3]
        data = {
            "products": [f"{product.name} ({product.measurement_value}{product.volume_type})" for product in products],
            "cost_prices": [product.buy_price for product in products],
            "max_profits": [product.max_profit for product in products],
            "min_profits": [product.min_profit for product in products]
        }
    else:
        data = {"error": "Invalid data type requested."}

    return JsonResponse(data, safe=False)

@login_required
def inventory_chart_detail(request):
    """
    Returns detailed data for a specific inventory chart.
    Expected GET parameter:
      - chart: The type of chart (e.g., 'expiring_soon', 'low_stock', 'top_selling', 'stock_value', 'most_profitable', 'least_profitable').
    """
    chart_type = request.GET.get('chart', '')

    if chart_type == 'expiring_soon':
        stocks = Stocks.objects.filter(expiry_date__lte=timezone.now().date() + timedelta(days=7), status=1)
        data = {
            "products": [f"{stock.product_id.name}" for stock in stocks],
            "batch_numbers": [stock.batch_number for stock in stocks],
            "quantities": [stock.quantity for stock in stocks],
            "expiry_dates": [stock.expiry_date.strftime('%Y-%m-%d') for stock in stocks]
        }

    elif chart_type == 'low_stock':
        stocks = Stocks.objects.filter(quantity__lte=10).order_by('quantity')
        data = {
            "products": [f"{stock.product_id.name} ({stock.product_id.get_volume()})" for stock in stocks],
            "batch_numbers": [stock.batch_number for stock in stocks],
            "quantities": [stock.quantity for stock in stocks],
            "suppliers": [stock.supplier_id.name if stock.supplier_id else "Unknown" for stock in stocks]
        }

    elif chart_type == 'top_selling':
        top_selling = salesItems.objects.values(
            "product_id__name", "product_id__measurement_value", "product_id__volume_type"
        ).annotate(total_sold=Sum("qty")).order_by("-total_sold")
        data = {
            "products": [f'{item["product_id__name"]} ({item["product_id__measurement_value"]}{item["product_id__volume_type"]})' for item in top_selling],
            "quantities": [item["total_sold"] for item in top_selling]
        }

    elif chart_type == 'stock_value':
        categories = Category.objects.all()
        data = {
            "categories": [category.name for category in categories],
            "values": [
                Stocks.objects.filter(product_id__category_id=category).aggregate(
                    total_value=Sum(
                        Case(
                            When(quantity__gt=0, then=(F('cost_price') / F('quantity')) * F('quantity')),
                            default=Value(0.0, output_field=FloatField()),
                            output_field=FloatField()
                        )
                    )
                )['total_value'] or 0 for category in categories
            ]
        }

    elif chart_type == 'most_profitable':
        products = Products.objects.annotate(
            max_profit=(F('max_sell_price') - F('buy_price')),
            min_profit=(F('min_sell_price') - F('buy_price'))
        ).order_by('-max_profit')
        data = {
            "products": [f"{product.name} ({product.measurement_value}{product.volume_type})" for product in products],
            "cost_prices": [product.buy_price for product in products],
            "max_profits": [product.max_profit for product in products],
            "min_profits": [product.min_profit for product in products]
        }

    elif chart_type == 'least_profitable':
        products = Products.objects.annotate(
            max_profit=(F('max_sell_price') - F('buy_price')),
            min_profit=(F('min_sell_price') - F('buy_price'))
        ).order_by('max_profit')
        data = {
            "products": [f"{product.name} ({product.measurement_value}{product.volume_type})" for product in products],
            "cost_prices": [product.buy_price for product in products],
            "max_profits": [product.max_profit for product in products],
            "min_profits": [product.min_profit for product in products]
        }

    else:
        data = {"error": "Invalid chart type requested."}

    return JsonResponse(data, safe=False)

@login_required
def suppliers(request):
    if request.user.is_authenticated:
        suppliers = Supplier.objects.all()
        
        supplier_list = [{
            "id": supplier.id, "name":supplier.name, "email":supplier.email, "phone_number":supplier.phone_number,
            "address": supplier.address, "status": supplier.status
        } for supplier in suppliers]
        context = {
            "suppliers": suppliers,
            #"json": json.dumps(supplier_list),
            "page": "Suppliers"
        }
        return render(request, "posApp/inventory/suppliers.html", context)
    else:
        return redirect("pos-page")

@login_required
def stocks(request):
    if request.user.is_authenticated:
        products = Products.objects.all()
        suppliers = Supplier.objects.all()
        stocks = Stocks.objects.all()
        stock_list = [{
            "id": stock.id, "batch_number": stock.batch_number, "product_id": stock.product_id.id,
            "product_name": stock.product_id.name,
            "supplier_id": stock.supplier_id.id if stock.supplier_id else None,  # Handle None
            "supplier_name": stock.supplier_id.name if stock.supplier_id else "",  # Handle None
            "expiry_date": stock.expiry_date,
            "quantity": stock.quantity, "cost_price": stock.cost_price, "status": stock.status,
            "delivery_date": stock.delivery_date, "date_updated": stock.date_updated
        } for stock in stocks]
        
        context = {
            "stocks": stocks,
            "products": products,
            "suppliers": suppliers,
            "page": "Stocks",
            #"json": json.dumps(stock_list),
        }
        return render(request, "posApp/inventory/stocks.html", context)
    else:
        return redirect("pos-page")

@login_required
def manage_inventory(request):
    pass
    
@login_required
def search(request):
    """
    Returns data based on the search query.
    Expected GET parameter:
      - search_query
    """
    search_query = request.GET.get('q', '')
    search_scope = request.GET.get('scope', 'stock')  # Default to 'stock'

    if search_query and search_scope == "suppliers":
        suppliers = Supplier.objects.filter(name__icontains=search_query).values(
            "id", "name", "phone_number", "email", "address", "status"
        )
        return JsonResponse(list(suppliers), safe=False)
    elif search_scope == "suppliers":
        suppliers = Supplier.objects.all().values(
            "id", "name", "phone_number", "email", "address", "status"
        )
        return JsonResponse(list(suppliers), safe=False)
    
    elif search_query and search_scope == "stocks":
        stocks = Stocks.objects.filter(name__icontains=search_query).values(
            "id", "batch_number", "product_id", "supplier_id", "expiry_date", "quantity", "cost_price", "status"
        )
        return JsonResponse(list(stocks), safe=False)
    elif search_scope == "suppliers":
        stocks = Stocks.objects.filter(name__icontains=search_query).values(
            "id", "batch_number", "product_id", "supplier_id", "expiry_date", "quantity", "cost_price", "status"
        )
        return JsonResponse(list(stocks), safe=False)
    elif search_query and search_scope == "products":
        products = Products.objects.filter(name__icontains=search_query).values(
            "id", "name", "measurement_value", "volume_type", "quantity", "buy_price", "sell_price"
        )
        return JsonResponse(list(products), safe=False)
    elif search_scope == "products":
        products = Products.objects.all().values(
            "id", "name", "measurement_value", "volume_type", "quantity", "buy_price", "sell_price"
        )
        return JsonResponse(list(products), safe=False)
    elif search_query and search_scope == "categories":
        categories = Category.objects.filter(name__icontains=search_query).values(
            "id", "name"
        )
        return JsonResponse(list(categories), safe=False)
    elif search_scope == "categories":
        categories = Category.objects.all().values(
            "id", "name"
        )
        return JsonResponse(list(categories), safe=False)
    else:
        return JsonResponse([], safe=False)

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
        hourly_sales = sales.annotate(
            hour=ExtractHour('date_added')
        ).values('hour').annotate(
            hourly_total=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()),
            hourly_cost=Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField()),
            hourly_profit=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()) - 
                          Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField())
        ).order_by('hour')

        sales_trend = {
            "hours": [record['hour'] for record in hourly_sales],
            "amounts": [record['hourly_total'] or 0 for record in hourly_sales],  # Handle None
            "costs": [record['hourly_cost'] or 0 for record in hourly_sales],    # Handle None
            "profits": [record['hourly_profit'] or 0 for record in hourly_sales] # Handle None
        }

        # Revenue breakdown by payment method.
        revenue = sales.aggregate(
            cash=Sum(
                Case(
                    When(payment_method='cash', then=F('grand_total')),
                    When(payment_method='both', then=F('cash_amount')),
                    default=Value(0.0, output_field=FloatField()),
                    output_field=FloatField()
                )
            ),
            mpesa=Sum(
                Case(
                    When(payment_method='mpesa', then=F('grand_total')),
                    When(payment_method='both', then=F('mpesa_amount')),
                    default=Value(0.0, output_field=FloatField()),
                    output_field=FloatField()
                )
            ),
            total=Sum('grand_total')
        )
        revenue = {k: v or 0 for k, v in revenue.items()}  # Handle None in aggregation results
        
        # Top selling products for the day.
        top_selling = salesItems.objects.filter(sale_id__date_added__date=date_value).values(
            "product_id__measurement_value", "product_id__volume_type", "product_id__name"
        ).annotate(total_sold=Coalesce(Sum("qty"), Value(0.0, output_field=FloatField()), output_field=FloatField())).order_by("-total_sold")[:5]
        top_selling_data = {
            "products": [
                f"{item['product_id__name']} ({item['product_id__measurement_value']}{item['product_id__volume_type']})"
                for item in top_selling
            ],
            "quantities": [item["total_sold"] for item in top_selling]
        }
        return {"sales_trend": sales_trend, "revenue": revenue, "top_selling": top_selling_data}

    # Determine the date(s) for which to generate the report.
    if 'report_date' in request.GET:
        report_date = request.GET.get('report_date')
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
            sales_trend["amounts"].append(sum(filter(None, daily_trend["amounts"])))  # Filter None
            sales_trend["costs"].append(sum(filter(None, daily_trend["costs"])))      # Filter None
            sales_trend["profits"].append(sum(filter(None, daily_trend["profits"])))  # Filter None

            daily_revenue = data["revenue"]
            revenue["cash"] += daily_revenue.get("cash", 0)
            revenue["mpesa"] += daily_revenue.get("mpesa", 0)
            revenue["revenue"] += daily_revenue.get("revenue", 0)

            # Update the counter for top-selling products.
            daily_top = data["top_selling"]
            for product, qty in zip(daily_top["products"], daily_top["quantities"]):
                top_counter[product] += qty or 0  # Handle None

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

    # Stock Levels: fetch products with the lowest quantity.
    stock_levels = Products.objects.values("code", "name", "measurement_value", "volume_type").annotate(
        stock=Coalesce(Sum("quantity"), Value(0.0, output_field=FloatField()), output_field=FloatField())
    ).order_by("stock")[:5]
    stock_levels_data = {
        "products": [
            f"{item['name']} ({item['measurement_value']}{item['volume_type']})"
            for item in stock_levels
        ],
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

@login_required
def chart_detail(request):
    data = {"detail": {}}
    chart = request.GET.get('chart')

    if "report_date" in request.GET:
        report_date = request.GET.get('report_date')
        try:
            date_value = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid report_date format. Expected YYYY-MM-DD."}, status=400)
        sales = Sales.objects.filter(date_added__date=date_value)

        if chart == 'revenue':
            revenue = sales.aggregate(
                cash=Coalesce(Sum(
                    Case(
                        When(payment_method='cash', then=F('grand_total')),
                        When(payment_method='both', then=F('cash_amount')),
                        default=Value(0.0, output_field=FloatField()),
                        output_field=FloatField()
                    )
                ), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                cash_amount=Coalesce(Sum(
                    Case(
                        When(payment_method='both', then=F('cash_amount')),
                        default=Value(0.0, output_field=FloatField()),
                        output_field=FloatField()
                    )
                ), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                mpesa=Coalesce(Sum(
                    Case(
                        When(payment_method='mpesa', then=F('grand_total')),
                        When(payment_method='both', then=F('mpesa_amount')),
                        default=Value(0.0, output_field=FloatField()),
                        output_field=FloatField()
                    )
                ), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                mpesa_amount=Coalesce(Sum(
                    Case(
                        When(payment_method='both', then=F('mpesa_amount')),
                        default=Value(0.0, output_field=FloatField()),
                        output_field=FloatField()
                    )
                ), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                total=Coalesce(Sum('grand_total'), Value(0.0, output_field=FloatField()), output_field=FloatField())
            )
            sales_data = []
            for sale in sales:
                sales_data.append({
                    "id": sale.id,
                    "code": sale.code,
                    "payment_method": sale.payment_method,
                    "grand_total": sale.grand_total,
                })
            data["chart"] = chart
            data["revenue"] = revenue
            data["detail"]["sales"] = sales_data

        elif chart == 'sales_trend':
            cost_expression = ExpressionWrapper(
                F('salesitems__product_id__buy_price') * F('salesitems__qty'),
                output_field=FloatField()
            )
            hourly_sales = sales.annotate(
                hour=ExtractHour('date_added')
            ).values('hour').annotate(
                sales_revenue=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                cost=Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                profit=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()) - 
                       Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField())
            ).order_by('hour')
            data["chart"] = chart
            data["detail"]["hourly"] = list(hourly_sales)

        elif chart == 'top_selling':
            top_selling = salesItems.objects.filter(sale_id__date_added__date=date_value).values(
                "product_id__measurement_value", "product_id__volume_type", "product_id__name"
            ).annotate(total_sold=Coalesce(Sum("qty"), Value(0.0, output_field=FloatField()), output_field=FloatField())).order_by("-total_sold")[:10]
            data["chart"] = chart
            data["top_selling"] = {
                "products": [
                    f"{item['product_id__name']} ({item['product_id__measurement_value']}{item['product_id__volume_type']})"
                    for item in top_selling
                ],
                "quantities": [item["total_sold"] for item in top_selling]
            }

        elif chart == 'stock':
            stock_levels = Products.objects.values("code", "name", "measurement_value", "volume_type").annotate(
                stock=Coalesce(Sum("quantity"), Value(0.0, output_field=FloatField()), output_field=FloatField())
            ).order_by("stock")
            data["chart"] = chart
            data["stock_levels"] = {
                "products": [
                    f"{item['name']} ({item['measurement_value']}{item['volume_type']})"
                    for item in stock_levels
                ],
                "quantities": [item["stock"] for item in stock_levels]
            }

        else:
            data["chart"] = chart
            data["detail"] = {"message": "Invalid chart type for single day report."}

    elif "start_date" in request.GET and "end_date" in request.GET:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date format. Expected YYYY-MM-DD."}, status=400)

        date_sales = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            date_sales[date_str] = Sales.objects.filter(date_added__date=current_date)
            current_date += timedelta(days=1)

        if chart == 'revenue':
            revenue = {"cash": 0, "mpesa": 0, "total": 0}
            detail = {}
            for date_str, sales_qs in date_sales.items():
                daily_revenue = sales_qs.aggregate(
                    cash=Sum(
                        Case(
                            When(payment_method='cash', then=F('grand_total')),
                            When(payment_method='both', then=F('cash_amount')),
                            default=Value(0.0, output_field=FloatField()),
                            output_field=FloatField()
                        )
                    ), 
                    mpesa=Sum(
                        Case(
                            When(payment_method='mpesa', then=F('grand_total')),
                            When(payment_method='both', then=F('mpesa_amount')),
                            default=Value(0.0, output_field=FloatField()),
                            output_field=FloatField()
                        )
                    ),
                    total=Sum('grand_total')
                )
                revenue["cash"] += daily_revenue.get("cash") or 0
                revenue["mpesa"] += daily_revenue.get("mpesa") or 0
                revenue["total"] += daily_revenue.get("total") or 0

                sales_list = []
                for sale in sales_qs:
                    items_qs = salesItems.objects.filter(sale_id=sale.id)
                    sale_items = list(items_qs.values())
                    sales_list.append({
                        "id": sale.id,
                        "code": sale.code,
                        "payment_method": sale.payment_method,
                        "grand_total": sale.grand_total,
                        "sale_items": sale_items,
                    })
                detail[date_str] = sales_list
            data["chart"] = chart
            data["revenue"] = revenue
            data["detail"] = detail

        elif chart == 'sales_trend':
            cost_expression = ExpressionWrapper(
                F('salesitems__product_id__buy_price') * F('salesitems__qty'),
                output_field=FloatField()
            )
            detail = {}
            for date_str, sales_qs in date_sales.items():
                hourly_sales = sales_qs.annotate(
                    hour=ExtractHour('date_added')
                ).values('hour').annotate(
                    sales_revenue=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                    cost=Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField()),
                    profit=Coalesce(Sum('grand_total', distinct=True), Value(0.0, output_field=FloatField()), output_field=FloatField()) - 
                           Coalesce(Sum(cost_expression), Value(0.0, output_field=FloatField()), output_field=FloatField())
                ).order_by('hour')
                detail[date_str] = list(hourly_sales)
            data["chart"] = chart
            data["detail"] = detail

        elif chart == 'top_selling':
            top_counter = Counter()
            for date_str, sales_qs in date_sales.items():
                daily_top = salesItems.objects.filter(sale_id__in=sales_qs).values(
                    "product_id_id__measurement_value", "product_id_id__volume_type", "product_id__name"
                ).annotate(total_sold=Coalesce(Sum("qty"), Value(0.0, output_field=FloatField()), output_field=FloatField()))
                for item in daily_top:
                    product_key = f"{item['product_id__name']} ({item['product_id_id__measurement_value']}{item['product_id_id__volume_type']})"
                    top_counter[product_key] += item["total_sold"]
            sorted_top = top_counter.most_common(10)
            data["chart"] = chart
            data["top_selling"] = {
                "products": [item[0] for item in sorted_top],
                "quantities": [item[1] for item in sorted_top]
            }

        elif chart == 'stock':
            stock_levels = Products.objects.values("code", "name", "measurement_value", "volume_type").annotate(
                stock=Coalesce(Sum("quantity"), Value(0.0, output_field=FloatField()), output_field=FloatField())
            ).order_by("stock")[:5]
            data["chart"] = chart
            data["stock_levels"] = {
                "products": [
                    f"{item['name']} ({item['measurement_value']}{item['volume_type']})"
                    for item in stock_levels
                ],
                "quantities": [item["stock"] for item in stock_levels]
            }

        else:
            data["chart"] = chart
            data["detail"] = {"message": "Invalid chart type for date range report."}

    else:
        data["detail"] = {"message": "No valid date parameters provided."}

        # ── strip out any date‐keys whose detail list is empty ──
    if isinstance(data.get('detail'), dict):
        data['detail'] = {
            date: items
            for date, items in data['detail'].items()
            if items  # only keep dates with a non-empty list
        }

    return JsonResponse(data, safe=False)
