import logging, json
from pickle import FALSE
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from flask import jsonify
from posApp.models import Category, Products, Sales, salesItems, Report, MpesaPaymentTransaction, Supplier, Stocks
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField, Case, When, Value
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from datetime import date, datetime, timedelta
from django.template.loader import render_to_string
from .mpesa import MpesaClient

logger = logging.getLogger(__name__)

# Login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

# Create your views here.
@login_required
def home(request):
    if request.user.is_superuser:
        now = datetime.now()
        current_year = now.strftime("%Y")
        current_month = now.strftime("%m")
        current_day = now.strftime("%d")
        categories = Category.objects.count()
        products = Products.objects.count()
        transaction = Sales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ).count()
        today_sales = Sales.objects.filter(
            date_added__year=current_year,
            date_added__month = current_month,
            date_added__day = current_day
        ).all()
        total_sales = sum(today_sales.values_list('grand_total',flat=True))
        context = {
            'page_title':'Home',
            'categories' : categories,
            'products' : products,
            'transaction' : transaction,
            'total_sales' : total_sales,
            "today": datetime.now().date(),
        }
        return render(request, 'posApp/home-alt.html',context)

    else:
        return redirect("pos-page")


def about(request):
    context = {
        'page_title':'About',
    }
    return render(request, 'posApp/about.html',context)

#Categories
@login_required
def category(request):
    category_list = Category.objects.all()
    # category_list = {}
    context = {
        'page_title':'Category List',
        'category':category_list,
    }
    return render(request, 'posApp/category.html',context)

@login_required
def manage_category(request):
    category = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()
    
    context = {
        'category' : category,
    }
    return render(request, 'posApp/manage_category.html',context)

@login_required
def save_category(request):
    data = request.POST
    print(f"\n{data}\n")
    resp = {'status': 'failed'}
    try:
        if data['id'].isnumeric() and int(data['id']) > 0:
            Category.objects.filter(id=data['id']).update(
                name=str.capitalize(data['name']),
                #description=data['description'],
                status=data['status']
            )
        else:
            if Category.objects.filter(name=str.capitalize(data['name'])).exists():
                resp['msg'] = "Category Already Exists in the database"
                return HttpResponse(json.dumps(resp), content_type="application/json")
            
            new_category = Category(
                name=str.capitalize(data['name']),
                #description=data['description'],
                status=data['status']
            )
            new_category.save()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully saved.')
    except Exception as e:
        print(f"Error: {e}")
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_category(request):
    data =  request.POST
    resp = {'status':''}
    try:
        Category.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

# Products
@login_required
def products(request):
    product_list = Products.objects.all()
    context = {
        'page_title':'Medicine List',
        'products':product_list,
    }
    return render(request, 'posApp/products.html',context)

@login_required
def manage_products(request):
    product = {}
    categories = Category.objects.filter(status = 1).all()
    volume_type = Products.VolumeType
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()
            print(f"quantity: {product.quantity}")
            product.quantity = int(product.quantity)
    
    context = {
        'product' : product,
        'volume_type': volume_type,
        'categories' : categories
    }
    return render(request, 'posApp/manage_product.html',context)

def test(request):
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return render(request, 'posApp/test.html',context)

@login_required
def save_product(request):
    data = request.POST
    resp = {'status': 'failed'}
    id = data.get('id', '')

    if id.isnumeric() and int(id) > 0:
        check = Products.objects.exclude(id=id).filter(code=data['code']).all()
    else:
        check = Products.objects.filter(code=data['code']).all()

    if check.exists():
        resp['msg'] = "Medicine Code Already Exists in the database"
    else:
        category = Category.objects.filter(id=data['category_id']).first()
        try:
            if id.isnumeric() and int(id) > 0:
                if int(data['available_quantity']) > 0 and float(data['buy_price']) > 0:
                    status = 1
                else:
                    status = 0
                    
                Products.objects.filter(id=id).update(
                    code=data['code'],
                    category_id=category,
                    name=str.capitalize(data['name']),
                    #description=data['description'],
                    volume_type = data['volume_type'],
                    measurement_value=int(data['measurement_value']),
                    quantity=data['available_quantity'],
                    buy_price=float(data['buy_price']),
                    min_sell_price=float(data['min_sell_price']),
                    max_sell_price=float(data['max_sell_price']),
                    status=status
                )
            else:
                new_product = Products(
                    code=data['code'],
                    category_id=category,
                    name=str.capitalize(data['name']),
                    #description=data['description'],
                    volume_type = data['volume_type'],
                    measurement_value=int(data['measurement_value']),
                    quantity=data['available_quantity'],
                    buy_price=float(data['buy_price']),
                    min_sell_price=float(data['min_sell_price']),
                    max_sell_price=float(data['max_sell_price']),
                    status=1
                )
                new_product.save()

            resp['status'] = 'success'
            messages.success(request, 'Medicine Successfully saved.')
        except Exception as e:
            logger.error(f"Error saving medicine: {e}")
            resp['status'] = 'failed'
            resp['msg'] = 'An error occurred while saving the medicine.'

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_product(request):
    data = request.POST
    resp = {'status': 'failed'}
    try:
        Products.objects.filter(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Medicine Successfully deleted.')
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        resp['msg'] = 'An error occurred while deleting the medicine.'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def pos(request):
    # Ensure URLs are registered only once
    if not hasattr(pos, "_urls_registered"):
        mpesa_client = MpesaClient()
        mpesa_client.register_urls()
        pos._urls_registered = True

    products = Products.objects.filter(status=1)
    context = {
        'page_title': "Point of Sale",
        'products': products,
    }
    return render(request, 'posApp/pos.html', context)

@login_required
def get_product_json(request):     
    try:
        products = Products.objects.filter(status=1)
        product_json = [{'id': product.id, 'name': product.name, 'volume': product.volume_type, 'value': product.measurement_value, 'buy_price': float(product.buy_price), 'min_sell_price': float(product.min_sell_price), 'max_sell_price': float(product.max_sell_price)} for product in products]
        return JsonResponse(product_json, safe=False)
    
    except Exception as e:
        logger.error(f"Error fetching product JSON: {e}")
        return JsonResponse({"error": "Couldn't get Products json"}, status=500)
    

@login_required
def checkout_modal(request):
    grand_total = request.GET.get('grand_total', 0)
    context = {
        'grand_total': grand_total,
    }
    return render(request, 'posApp/checkout.html', context)

@csrf_exempt
@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST

    def generate_sale_code():
        pref = datetime.now().year + datetime.now().year
        i = 1
        while True:
            code = '{:0>5}'.format(i)
            i += 1
            if not Sales.objects.filter(code=str(pref) + str(code)).exists():
                break
        code = str(pref) + str(code)
        return code

    try:
        print(f"{data}")
        
        # Validate payment method
        payment_method = data.get('payment_method')
        mpesa_transaction_code = data.get('mpesa_code', '').strip()

        if payment_method == 'mpesa':
            if not mpesa_transaction_code:
                resp['msg'] = "M-Pesa transaction code is required for M-Pesa payments."
                return JsonResponse(resp)

            # Ensure the transaction code is in uppercase
            mpesa_transaction_code = mpesa_transaction_code.upper()

            # Check for duplicate M-Pesa transaction code
            if Sales.objects.filter(mpesa_transaction_code=mpesa_transaction_code).exists():
                resp['msg'] = "The M-Pesa transaction code already exists. Please use a unique code."
                return JsonResponse(resp)

        # Create a new Sales record
        sale = Sales(
            code=generate_sale_code(),
            sub_total=data['sub_total'],
            tax=data['tax'],
            tax_amount=data['tax_amount'],
            grand_total=data['grand_total'],
            tendered_amount=data['tendered_amount'],
            amount_change=data['amount_change'],
            payment_method=payment_method,
            mpesa_transaction_code=mpesa_transaction_code if payment_method == 'mpesa' else '',
            served_by=request.user
        )
        sale.save()

        # Process each product in the sale
        for i, product_id in enumerate(data.getlist('product_id[]')):
            qty = float(data.getlist('qty[]')[i])
            price = float(data.getlist('price[]')[i])
            product = Products.objects.get(id=product_id)

            # Find the stock batch with sufficient quantity
            stock = Stocks.objects.filter(product_id=product, quantity__gte=qty).order_by('expiry_date').first()
            if not stock:
                raise Exception(f"Insufficient stock for product {product.name}")

            # Reduce stock quantity
            stock.quantity -= qty
            stock.save()

            # Create a sales item linked to the stock batch
            sales_item = salesItems(
                sale_id=sale,
                product_id=product,
                stock_id=stock,
                qty=qty,
                price=price,
                total=qty * price
            )
            sales_item.save()

        resp['status'] = 'success'
        resp['sale_id'] = sale.id
        messages.success(request, "Sale record has been saved.")
    except Exception as e:
        logger.error(f"Error saving POS: {e}")
        resp['msg'] = str(e)

    return JsonResponse(resp)

@login_required
def salesList(request):
    payment_method = request.GET.get('payment_method', '')  # Get filter parameter
    sales = Sales.objects.all()

    if payment_method and payment_method in dict(Sales.PaymentMethod.choices):  # Validate filter
        sales = sales.filter(payment_method=payment_method)

    sale_data = []
    for sale in sales:
        data = {field.name: getattr(sale, field.name) for field in sale._meta.get_fields(include_parents=False) if field.related_model is None}
        data['items'] = salesItems.objects.filter(sale_id=sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']), '.2f')
        sale_data.append(data)

    context = {
        'page_title': 'Sales Transactions',
        'sale_data': sale_data,
        'payment_methods': Sales.PaymentMethod.choices,  # Pass payment methods for dropdown
        'selected_method': payment_method  # Keep track of selected method
    }
    return render(request, 'posApp/sales.html', context)

@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id=id).first()
    transaction = {field.name: getattr(sales, field.name) for field in Sales._meta.get_fields() if field.related_model is None}
    transaction['served_by'] = str.capitalize(sales.served_by.username)
    transaction['payment_method'] = str.capitalize(sales.payment_method)
    transaction['mpesa_code'] = str.upper(sales.mpesa_transaction_code)
    if 'tax_amount' in transaction:
        transaction['tax_amount'] = format(float(transaction['tax_amount']), '.2f')
    ItemList = salesItems.objects.filter(sale_id=sales).all()
    context = {
        "transaction": transaction,
        "salesItems": ItemList
    }
    return render(request, 'posApp/receipt.html', context)

@login_required
def delete_sale(request):
    resp = {'status': 'failed', 'msg': ''}
    id = request.POST.get('id')
    try:
        Sales.objects.filter(id=id).delete()
        resp['status'] = 'success'
        messages.success(request, 'Sale Successfully deleted.')
    except Exception as e:
        logger.error(f"Error deleting sale: {e}")
        resp['msg'] = 'An error occurred while deleting the sale.'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def reports(request):
    try:
        reports = Report.objects.all()
    
    except:        
        reports = Report.objects.none()
     
    context = {
        'reports': reports,
    }
    return render(request, 'posApp/reports.html', context)


@login_required
def reports_view(request):
    context = {
        "page_title": "Reports"
    }
    return render(request, "posApp/report/reports.html", context)

@login_required
def reports_data(request):
    today = datetime.today().astimezone()
    
    # Sales Trends (Last 7 Days)
    sales_trends = Sales.objects.filter(date_added__gte= today - timedelta(days=1))
    trends_data = sales_trends.values_list("date_added__date").annotate(amount=Sum("grand_total"))
    sales_trends_data = {
        "dates": [str(data[0]) for data in trends_data],
        "amounts": [data[1] for data in trends_data]
    }
    
    # Revenue Breakdown
    revenue_breakdown = Sales.objects.aggregate(
        cash=Sum(Case(When(payment_method="cash", then=F("grand_total")), default=Value(0), output_field=FloatField())),
        mpesa=Sum(Case(When(payment_method="mpesa", then=F("grand_total")), default=Value(0), output_field=FloatField()))
    )
    
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
        "revenue_breakdown": [revenue_breakdown["cash"] or 0, revenue_breakdown["mpesa"] or 0],
        "top_selling": top_selling_data,
        "stock_levels": stock_levels_data,
    }
    return JsonResponse(data)

@login_required
def generate_report(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        report_type = data.get('report_type', 'sales')
        time_period = data.get('time_period', 'daily')
        payment_method = data.get('payment_method', 'all')  # Default to all

        today = datetime.now().astimezone()

        # Set time period range
        if time_period == 'daily':
            time_range = Report.ReportTimeRange.DAILY
            start_date = today - timedelta(days=1)
        elif time_period == 'weekly':
            time_range = Report.ReportTimeRange.WEEKLY
            start_date = today - timedelta(weeks=1)
        elif time_period == 'monthly':
            time_range = Report.ReportTimeRange.MONTHLY 
            start_date = today - timedelta(weeks=4)
        elif time_period == 'annual':
            time_range = Report.ReportTimeRange.ANNUAL
            start_date = today - timedelta(weeks=52)
        else:
            start_date = today

        if report_type == "inventory":
            products = Products.objects.all()
            report_data = [
                {
                    "product_code": product.code,
                    "product_name": product.name,
                    "category": product.category_id.name,
                    "description": product.description,
                    "measurement_type": product.measurement_value.name if product.measurement_value else "",
                    "buy_price": product.buy_price,
                    "min_sell_price": product.min_sell_price,
                    "max_sell_price": product.max_sell_price,
                    "available_quantity": product.quantity,
                    "status": product.status,
                    "date_added": product.date_added.isoformat(),
                    "date_updated": product.date_updated.isoformat(),
                }
                for product in products
            ]

            report = Report(
                name="Inventory Report " + str(today),
                generated_by=request.user,
                type=Report.ReportType.INVENTORY,
                json=json.dumps(report_data)
            )
            report.save()
        else:
            # Sales Report
            # Filter sales based on the time range
            sales = Sales.objects.filter(date_added__gte=start_date)
            
            # Apply payment method filter if needed
            if (payment_method in dict(Sales.PaymentMethod.choices)):
                sales = sales.filter(payment_method=payment_method)

            total_sales_amount = sales.aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0

            # Filter salesItems to only include items belonging to the filtered sales
            filtered_salesitems = salesItems.objects.filter(sale_id__in=sales)

            # Calculate Most Profitable Products
            most_profitable_products = filtered_salesitems.values(
                'product_id__code', 'product_id__name', 'product_id__description', 
                'product_id__buy_price', 'price'
            ).annotate(
                total_quantity=Sum('qty'),
                total_amount=Sum(F('qty') * F('price')),
                total_profit=Sum(ExpressionWrapper(
                    F('qty') * (F('price') - F('product_id__buy_price')),
                    output_field=FloatField()
                )),
                total_percentage_profit=ExpressionWrapper(
                    (Sum(ExpressionWrapper(
                        F('qty') * (F('price') - F('product_id__buy_price')),
                        output_field=FloatField()
                    )) / Sum(F('qty') * F('product_id__buy_price'))) * 100,
                    output_field=FloatField()
                )
            ).order_by('-total_percentage_profit')

            # Calculate Products with Most Sold Quantity
            products_with_most_sales = filtered_salesitems.values(
                'product_id__code', 'product_id__name', 'product_id__description', 
                'product_id__buy_price', 'price'
            ).annotate(
                total_quantity=Sum('qty'),
                total_amount=Sum(F('qty') * F('price')),
                total_profit=Sum(ExpressionWrapper(
                    F('qty') * (F('price') - F('product_id__buy_price')),
                    output_field=FloatField()
                )),
                total_percentage_profit=ExpressionWrapper(
                    (Sum(ExpressionWrapper(
                        F('qty') * (F('price') - F('product_id__buy_price')),
                        output_field=FloatField()
                    )) / Sum(F('qty') * F('product_id__buy_price'))) * 100,
                    output_field=FloatField()
                )
            ).order_by('-total_quantity')

            report_data = {
                "total_sales_amount": total_sales_amount,
                "most_profitable_products": list(most_profitable_products),
                "products_with_most_sales": list(products_with_most_sales),
                "sales": [
                    {
                        "sale_code": sale.code,
                        "date_of_sale": sale.date_added.isoformat(),
                        "sub_total": sale.sub_total,
                        "grand_total": sale.grand_total,
                        "tax": (sale.tax_amount / sale.sub_total * 100) if sale.sub_total > 0 else 0,
                        "tax_amount": sale.tax_amount,
                        "tendered_amount": sale.tendered_amount,
                        "amount_change": sale.amount_change,
                        "payment_method": sale.payment_method,
                        "items": [
                            {
                                "product_code": item.product_id.code,
                                "product_name": item.product_id.name,
                                "quantity": item.qty,
                                "buy_price": item.product_id.buy_price,
                                "price": item.price,
                                "total": item.total
                            }
                            for item in sale.salesitems_set.all()
                        ]
                    }
                    for sale in sales
                ]
            }

            report = Report(
                name=f"{time_range.capitalize()} Sales Report  - {payment_method.capitalize()} {today}",
                generated_by=request.user,
                type=Report.ReportType.SALES,
                time_range=time_range,
                json=json.dumps(report_data)
            )
            report.save()

        messages.success(request, 'Report Successfully Generated')
        return JsonResponse({"status": "success", "msg": "Report generated successfully."})
    
    return JsonResponse({"status": "failed", "msg": "Invalid request method."}, status=400)

@login_required
def get_report(request, id: int):
    try:
        report = Report.objects.get(id=id)
        report_data = {
            "name": report.name,
            "generated_on": report.generated_on.strftime("%Y-%m-%d %H:%M:%S"),
            "generated_by": report.generated_by,
            "type": report.type,
            "time_range": report.time_range,
            "json": json.loads(report.json)
        }
        if report.type == Report.ReportType.SALES:
            html = render_to_string('posApp/report/sales_report.html', {'report': report_data}, request)
        else:
            html = render_to_string('posApp/report/inventory_report.html', {'report': report_data}, request)
        
        return HttpResponse(html)
    except Report.DoesNotExist:
        return JsonResponse({"status": "failed", "msg": "Report not found"})
    except Exception as e:
        return JsonResponse({"error": str(e)})

@login_required
def delete_report(request):
    if request.method == "POST":
        data = json.loads(request.body)
        report_id = data.get('id')
        try:            
            Report.objects.filter(id=report_id).delete()            
            messages.success(request, 'Report Successfully deleted.')
            return HttpResponse(json.dumps({"status": "success", "msg": f"Report Deleted"}), content_type="application/json")
        except:
            return HttpResponse(json.dumps({"status": "failed", "msg": f"Could not delete report!"}), content_type="application/json") 
    
    else:
        
        messages.error(request, 'Could not delete report.')
        return HttpResponse(json.dumps({"status": "failed", "msg": "Invalid request method"}), content_type="application/json")

@csrf_exempt
def initiate_payment(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = float(request.POST.get('amount'))
        account_reference = f"Order{int(datetime.now().timestamp())}"  # Example of generating a reference
        
        # Create a PaymentTransaction record
        
        payment_transaction = MpesaPaymentTransaction.objects.create(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc="Test Payment for goods/services"
        )
        
        mpesa_client = MpesaClient()

        try:
            response = mpesa_client.express(phone_number, amount)
            print(f"\nLipa Request Response: {response}\n")
            
            payment_transaction.transaction_id = response['CheckoutRequestID']
            payment_transaction.status = "Pending"  # Set initial status as pending
            payment_transaction.mpesa_response = response  # Store the full M-Pesa response
            
            payment_transaction.save()
            
            print(f"\nTransaction Record : {payment_transaction}\n")
        except Exception as e:
            payment_transaction.status = "Failed"
            payment_transaction.save()
            return render(request, 'payment/payment_error.html', {'error': str(e)})

    return render(request, 'payment/payment_form.html')

@csrf_exempt
def payment_callback(request):
    """
    Handle M-Pesa STK push callback.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info("Payment callback received: %s", data)

            # Extract required fields
            result_code = data['Body']['stkCallback'].get('ResultCode')
            result_desc = data['Body']['stkCallback'].get('ResultDesc')
            checkout_request_id = data['Body']['stkCallback'].get('CheckoutRequestID')
            amount_received = data['Body']['stkCallback'].get('Amount', 0)
            transaction_time = data['Body']['stkCallback'].get('TransactionDate')

            # Validate required fields
            if result_code is None or result_desc is None or not checkout_request_id:
                logger.warning("Missing required fields in callback data")
                return JsonResponse({'status': 'failed', 'error': 'Invalid callback data'}, status=400)

            # Parse transaction time
            try:
                transaction_time = datetime.strptime(str(transaction_time), "%Y%m%d%H%M%S") if transaction_time else None
            except ValueError:
                logger.warning("Invalid transaction time format")
                return JsonResponse({'status': 'failed', 'error': 'Invalid transaction time format'}, status=400)

            # Find the transaction
            transaction = MpesaPaymentTransaction.objects.filter(transaction_id=checkout_request_id).first()
            if not transaction:
                logger.warning(f"Transaction with ID {checkout_request_id} not found")
                return JsonResponse({'status': 'failed', 'error': 'Transaction not found'}, status=404)

            # Update transaction details
            transaction.status = (
                MpesaPaymentTransaction.StatusChoices.COMPLETED
                if result_code == 0
                else MpesaPaymentTransaction.StatusChoices.CANCELLED
            )
            transaction.result_code = result_code
            transaction.result_desc = result_desc
            transaction.amount_received = amount_received
            transaction.transaction_time = transaction_time
            transaction.save()

            return JsonResponse({'status': 'success'})
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in payment_callback")
            return JsonResponse({'status': 'failed', 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error("Error in payment_callback: %s", str(e))
            return JsonResponse({'status': 'failed', 'error': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'invalid'}, status=400)

@csrf_exempt
def payment_validation(request):
    """
    Handle M-Pesa validation callback (typically for C2B).
    M-Pesa will POST a JSON payload to this endpoint to validate a transaction.
    We respond with a zero ResultCode to indicate acceptance.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            logger.info("Payment validation callback received: %s", data)
            """
            # (Optional) Insert any business validation logic here.
            response = {
                "ResultCode": 0,
                "ResultDesc": "Accepted"
            }
            """
            #return JsonResponse(response)
        except Exception as e:
            logger.error("Error in payment_validation: %s", str(e))
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Validation failed"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=400)
    
@csrf_exempt
def payment_confirmation(request):
    """
    Handle M-Pesa confirmation callback (for C2B payments).
    Extracts payment details and updates or creates a transaction record.
    """
    
    if request.method == "POST":
        print(f"Confirmation Post {request.POST.get()}")
        try:
            data = json.loads(request.body)
            logger.info("Payment confirmation callback received: %s", data)
            print(f"\nCallback:{data}\n")

            # Extract fields from the callback payload.
            transaction_type = data.get("TransactionType", "C2B")
            trans_id = data.get("TransID")
            trans_time = data.get("TransTime")
            trans_amount = data.get("TransAmount")
            bill_ref_number = data.get("BillRefNumber")  # POS number
            msisdn = data.get("MSISDN")

            # Handle customer name (some responses may not include a middle name)
            first_name = data.get("FirstName", "").strip()
            last_name = data.get("LastName", "").strip()
            customer_name = f"{first_name} {last_name}".strip()

            # Convert amount to decimal
            try:
                amount_received = float(trans_amount)
            except ValueError:
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid amount format"}, status=400)

            # Parse transaction time
            try:
                transaction_time = datetime.strptime(trans_time, "%Y%m%d%H%M%S") if trans_time else None
            except ValueError:
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid transaction time format"}, status=400)

            # Update or create the transaction record
            transaction, created = MpesaPaymentTransaction.objects.update_or_create(
                transaction_id=trans_id,
                defaults={
                    "customer_name": customer_name,
                    "phone_number": msisdn,
                    "amount_received": amount_received,
                    "account_reference": bill_ref_number,
                    "transaction_desc": transaction_type,
                    "transaction_time": transaction_time,
                    "status": MpesaPaymentTransaction.StatusChoices.COMPLETED,
                    "mpesa_response": data
                }
            )

            if created:
                logger.info(f"New payment recorded: {transaction}")
            else:
                logger.info(f"Updated existing payment record: {transaction}")

            # Respond to Safaricom
            response = {"ResultCode": 0, "ResultDesc": "Confirmation received successfully"}
            return JsonResponse(response)

        except Exception as e:
            logger.error(f"Error in payment_confirmation: {str(e)}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Error processing request"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=400)

@csrf_exempt
def payment_result(request):
    """
    Handle M-Pesa result callback for B2C/B2B transactions.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            logger.info("Payment result callback received: %s", data)
            
            result = data.get("Result", {})
            transaction_id = result.get("TransactionID")
            if not transaction_id:
                logger.warning("TransactionID missing in callback data")
                return JsonResponse({"ResultCode": 1, "ResultDesc": "TransactionID missing"}, status=400)

            # Find the corresponding transaction
            transaction = MpesaPaymentTransaction.objects.filter(transaction_id=transaction_id).first()
            if not transaction:
                logger.warning(f"Transaction with ID {transaction_id} not found")
                return JsonResponse({"ResultCode": 1, "ResultDesc": "Transaction not found"}, status=404)

            # Update transaction details
            transaction.status = "Success" if result.get("ResultCode") == 0 else "Failed"
            transaction.result_code = result.get("ResultCode")
            transaction.result_desc = result.get("ResultDesc")
            transaction.mpesa_response = data
            transaction.transaction_method = result.get("TransactionType", "B2C")
            transaction.save()

            response = {"ResultCode": 0, "ResultDesc": "Result processed successfully"}
            return JsonResponse(response)
        except json.JSONDecodeError:
            logger.error("Invalid JSON received in payment_result")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error("Error in payment_result: %s", str(e))
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Result processing failed"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=400)

@csrf_exempt
def payment_timeout(request):
    """
    Handle the M-Pesa Queue Timeout callback.
    M-Pesa will POST a JSON payload to this endpoint if a transaction
    remains in the queue longer than expected.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            logger.info("Payment timeout : %s", data)
            
            # Optionally, update a transaction record or take any additional actions.
            
            response = {
                "ResultCode": 0,
                "ResultDesc": "Timeout processed successfully"
            }
            return JsonResponse(response)
        except Exception as e:
            logger.error("Error processing payment timeout: %s", str(e))
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Timeout processing failed"}, status=500)
    else:
        return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid request method"}, status=400)
    
@csrf_exempt
def check_payment(request):
    """
    Check if a payment has been received based on the provided POS number (account_reference)
    and the payable amount (grand_total).
    """
    print(f"Check Mpesa Payment")
    if request.method == "POST":
        try:
            account_reference = request.POST.get("pos", "").strip()
            grand_total = request.POST.get("grand_total", "").strip()

            # Ensure required parameters are provided
            if not account_reference or not grand_total:
                return JsonResponse({"payment_confirmed": False, "error": "Missing required parameters"}, status=400)

            # Convert grand_total to Decimal for precision
            try:
                grand_total = Decimal(grand_total)
            except InvalidOperation:
                return JsonResponse({"payment_confirmed": False, "error": "Invalid grand_total format"}, status=400)

            # Query the payment transaction
            payment = MpesaPaymentTransaction.objects.filter(
                account_reference=account_reference,
                amount_received=grand_total,
                status=MpesaPaymentTransaction.StatusChoices.COMPLETED
            ).first()

            if payment:
                return JsonResponse({"success": True, "customer_name": payment.customer_name, "amount": float(payment.amount_received)})
            else:
                return JsonResponse({"success": False})
        except Exception as e:
            logger.error("Error checking payment: %s", str(e))
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Error processing request"}, status=500)
    else:
        return JsonResponse({"success": False}, status=401)

@login_required
def get_supplier(request):
    """
    Fetch a supplier's data by ID.
    """
    supplier_id = request.GET.get('id', '')
    supplier = get_object_or_404(Supplier, id=supplier_id)
    data = {
        "id": supplier.id,
        "name": supplier.name,
        "phone_number": supplier.phone_number,
        "email": supplier.email,
        "address": supplier.address,
        "status": supplier.status,
    }
    return JsonResponse(data)

@csrf_exempt
@login_required
def save_supplier(request):
    """
    Save or update a supplier.
    """
    if request.method == "POST":
        supplier_id = request.POST.get('supplierId')
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        address = request.POST.get('address')
        status = request.POST.get('status')
    
        if supplier_id:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier.name = name
            supplier.phone_number = phone_number
            supplier.email = email
            supplier.address = address
            supplier.status = status
            supplier.save()
        else:
            Supplier.objects.create(
                name=name,
                phone_number=phone_number,
                email=email,
                address=address,
                status=status,
            )
        messages.success(request, 'supplier created Successfully.')
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)

@login_required
def delete_supplier(request):
    if request.method == "POST":
        supplier_id = request.POST.get('id')
        if supplier_id:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier.delete()
            messages.success(request, 'Supplier deleted Successfully.')
            return JsonResponse({"success": True})
        else:
            messages.error(request, 'Supplier ID not provided.')
            return JsonResponse({"success": False, "error": "Supplier ID not provided"}, status=400)
    
        
    return JsonResponse({"success": False}, status=400)

@login_required
def stocks_page(request):
    context = {
        'page_title': 'Stocks',
        'stocks': Stocks.objects.select_related('product_id', 'supplier_id').all(),
        'products': Products.objects.filter(status=1),
        'suppliers': Supplier.objects.filter(status=1)
    }
    return render(request, 'posApp/inventory/stocks.html', context)

@login_required
def get_stock(request):
    stock_id = request.GET.get('id')
    try:
        stock = Stocks.objects.get(id=stock_id)
        data = {
            'product_id': stock.product_id.id,
            'supplier_id': stock.supplier_id.id,
            'batch_number': stock.batch_number,
            'quantity': stock.quantity,
            'cost_price': stock.cost_price,
            'expiry_date': stock.expiry_date.strftime('%Y-%m-%d') if stock.expiry_date else '',
        }
        return JsonResponse(data)
    except Stocks.DoesNotExist:
        return JsonResponse({'error': 'Stock not found'}, status=404)

@login_required
def save_stock(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'msg': 'Invalid request method'})

    stock_id = request.POST.get('id')
    
    try:
        if stock_id:
            # Update existing stock
            stock = Stocks.objects.get(id=stock_id)
        else:
            # Create new stock
            stock = Stocks()
        
        stock.product_id_id = request.POST.get('product_id')
        stock.supplier_id_id = request.POST.get('supplier_id')
        stock.batch_number = request.POST.get('batch_number')
        stock.quantity = float(request.POST.get('quantity'))
        stock.cost_price = float(request.POST.get('cost_price'))
        stock.expiry_date = request.POST.get('expiry_date')
        
        stock.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'failed', 'msg': str(e)})

@login_required
def delete_stock(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'msg': 'Invalid request method'})
        
    try:
        stock_id = request.POST.get('id')
        Stocks.objects.filter(id=stock_id).delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'failed', 'msg': str(e)})