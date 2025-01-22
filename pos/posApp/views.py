import logging, json
from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from flask import jsonify
from posApp.models import Category, Products, Sales, salesItems, MeasurementType, Report
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from datetime import date, datetime, timedelta
from django.template.loader import render_to_string

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
    now = datetime.now()
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")
    categories = len(Category.objects.all())
    products = len(Products.objects.all())
    transaction = len(Sales.objects.filter(
        date_added__year=current_year,
        date_added__month = current_month,
        date_added__day = current_day
    ))
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
    }
    return render(request, 'posApp/home.html',context)


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
    measurements = MeasurementType.MEASUREMENT_CHOICES
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()
    
    context = {
        'category' : category,
        'measurement_types': measurements,
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
                name=data['name'],
                description=data['description'],
                measurement_type=data['measurement_type'],
                status=data['status']
            )
        else:
            new_category = Category(
                name=data['name'],
                description=data['description'],
                measurement_type=data['measurement_type'],
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
        'page_title':'Product List',
        'products':product_list,
    }
    return render(request, 'posApp/products.html',context)

@login_required
def manage_products(request):
    product = {}
    categories = Category.objects.filter(status = 1).all()
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()
    
    context = {
        'product' : product,
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
        resp['msg'] = "Product Code Already Exists in the database"
    else:
        category = Category.objects.filter(id=data['category_id']).first()
        measurement_value = MeasurementType.objects.filter(id=data['measurement_value']).first()
        try:
            if id.isnumeric() and int(id) > 0:
                Products.objects.filter(id=id).update(
                    code=data['code'],
                    category_id=category,
                    name=data['name'],
                    description=data['description'],
                    measurement_value=measurement_value,
                    available_quantity=data['available_quantity'],
                    price=float(data['price']),
                    status=data['status']
                )
            else:
                new_product = Products(
                    code=data['code'],
                    category_id=category,
                    name=data['name'],
                    description=data['description'],
                    measurement_value=measurement_value,
                    available_quantity=data['available_quantity'],
                    price=float(data['price']),
                    status=data['status']
                )
                new_product.save()

            resp['status'] = 'success'
            messages.success(request, 'Product Successfully saved.')
        except Exception as e:
            logger.error(f"Error saving product: {e}")
            resp['status'] = 'failed'
            resp['msg'] = 'An error occurred while saving the product.'

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_product(request):
    data = request.POST
    resp = {'status': 'failed'}
    try:
        Products.objects.filter(id=data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Product Successfully deleted.')
    except Exception as e:
        logger.error(f"Error deleting product: {e}")
        resp['msg'] = 'An error occurred while deleting the product.'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def pos(request):
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
        product_json = [{'id': product.id, 'name': product.name, 'description': product.description, 'price': float(product.price)} for product in products]
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

@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    pref = datetime.now().year + datetime.now().year
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += 1
        if not Sales.objects.filter(code=str(pref) + str(code)).exists():
            break
    code = str(pref) + str(code)

    try:
        sales = Sales(code=code, sub_total=data['sub_total'], tax=data['tax'], tax_amount=data['tax_amount'], grand_total=data['grand_total'], tendered_amount=data['tendered_amount'], amount_change=data['amount_change'])
        sales.save()
        sale_id = sales.pk
        for i, prod in enumerate(data.getlist('product_id[]')):
            product = Products.objects.filter(id=prod).first()
            qty = data.getlist('qty[]')[i]
            price = data.getlist('price[]')[i]
            total = float(qty) * float(price)
            salesItems(sale_id=sales, product_id=product, qty=qty, price=price, total=total).save()
            
            # Update product quantity
            product.available_quantity = product.available_quantity - int(qty)
            if product.available_quantity == 0:
                product.status = 0
            product.save()
              
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        messages.success(request, "Sale Record has been saved.")
    except Exception as e:
        logger.error(f"Error saving POS: {e}")
        resp['msg'] = "An error occurred"
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def salesList(request):
    sales = Sales.objects.all()
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
    }
    return render(request, 'posApp/sales.html', context)

@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id=id).first()
    transaction = {field.name: getattr(sales, field.name) for field in Sales._meta.get_fields() if field.related_model is None}
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
def get_measurements(request, category_id):
    category = Category.objects.get(id=category_id)
    measurement_type = category.measurement_type
    measurements = MeasurementType.objects.filter(type=measurement_type)
    data = {
        'measurements': list(measurements.values('id', 'name', 'short_name'))
    }
    
    return HttpResponse(json.dumps(data), content_type="application/json")

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
@csrf_exempt
def generate_report(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        report_type = data.get('report_type', 'inventory')
        time_period = data.get('time_period', 'daily')

        if report_type == "inventory":
            products = Products.objects.all()
            report_data = [
                {
                    "product_code": product.code,
                    "product_name": product.name,
                    "category": product.category_id.name,
                    "description": product.description,
                    "measurement_type": product.measurement_value.name if product.measurement_value else "",
                    "price": product.price,
                    "available_quantity": product.available_quantity,
                    "status": product.status,
                    "date_added": product.date_added.isoformat(),
                    "date_updated": product.date_updated.isoformat(),
                }
                for product in products
            ]

            report = Report(
                name="Inventory Report " + str(datetime.now().astimezone()),
                type=Report.ReportType.INVENTORY,
                json=json.dumps(report_data)
            )
            report.save()

        else:
            today = datetime.now().astimezone()

            if time_period == 'daily':
                start_date = today - timedelta(days=1)
                time_range = Report.ReportTimeRange.DAILY
            elif time_period == 'weekly':
                start_date = today - timedelta(weeks=1)
                time_range = Report.ReportTimeRange.WEEKLY
            elif time_period == 'monthly':
                start_date = today - timedelta(weeks=4)
                time_range = Report.ReportTimeRange.MONTHLY
            elif time_period == 'annual':
                start_date = today - timedelta(weeks=52)
                time_range = Report.ReportTimeRange.ANNUAL
            else:
                start_date = today
                time_range = Report.ReportTimeRange.DAILY

            sales = Sales.objects.filter(date_added__gte=start_date).annotate(
                total_sales=Sum('grand_total'),
                tax_percentage=ExpressionWrapper(
                    (F('tax_amount') / F('sub_total')) * 100,
                    output_field=FloatField()
                )
            )
            report_data = [
                {
                    "sale_code": sale.code,
                    "date_of_sale": sale.date_added.isoformat(),
                    "sub_total": sale.sub_total,
                    "grand_total": sale.grand_total,
                    "tax_amount": sale.tax_amount,
                    "tendered_amount": sale.tendered_amount,
                    "amount_change": sale.amount_change,
                    "items": [
                        {
                            "product_code": item.product_id.code,
                            "product_name": item.product_id.name,
                            "quantity": item.qty,
                            "price": item.price,
                            "total": item.total
                        }
                        for item in sale.salesitems_set.all()
                    ]
                }
                for sale in sales
            ]

            report = Report(
                name=f"Sales Report {time_period.capitalize()} {str(datetime.now().astimezone())}",
                type=Report.ReportType.SALES,
                time_range=time_range,
                json=json.dumps(report_data)
            )
            report.save()

        return JsonResponse({"status": "success", "message": "Report generated successfully."})
    else:
        return JsonResponse({"status": "failed", "message": "Invalid request method."}, status=400)

@login_required
def get_report(request, id: int):
    try:
        report = Report.objects.get(id=id)
        report_data = {
            "name": report.name,
            "generated_on": report.generated_on.strftime("%Y-%m-%d %H:%M:%S"),
            "type": report.type,
            "json": json.loads(report.json)
        }
        if report.type == Report.ReportType.SALES:
            html = render_to_string('posApp/report/sales_report.html', {'report': report_data}, request)
        else:
            html = render_to_string('posApp/report/inventory_report.html', {'report': report_data}, request)
        
        return HttpResponse(html)
    except Report.DoesNotExist:
        return JsonResponse({"error": "Report not found"})
    except Exception as e:
        return JsonResponse({"error": str(e)})

@login_required
def delete_report(request):
    if request.method == "POST":
        data = json.loads(request.body)
        report_id = data.get('id')
        try:
            Report.objects.filter(id=report_id).delete()
            return HttpResponse(json.dumps({"status": "success", "message": "Report Deleted"}), content_type="application/json")
        except:
            return HttpResponse(json.dumps({"status": "failed", "message": "Could not delete report!"}), content_type="application/json") 
    
    else:
        return HttpResponse(json.dumps({"status": "failed", "message": "Invalid request method"}), content_type="application/json")
