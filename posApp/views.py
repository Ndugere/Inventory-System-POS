import logging, json
from pickle import FALSE
from decimal import Decimal, InvalidOperation
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from flask import jsonify
from django.contrib.auth.models import User
from posApp.models import Category, Products, Sales, salesItems, Report, MpesaPaymentTransaction, Supplier, Stocks, Expense, ExpenseCategory
from django.db.models import Count, Sum, F, ExpressionWrapper, FloatField, Case, When, Value, Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from datetime import date, datetime, timedelta
from django.template.loader import render_to_string
from django.core.paginator import Paginator
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
        return render(request, 'home-alt.html',context)

    else:
        return redirect("pos-page")

def about(request):
    context = {
        'page_title':'About',
    }
    return render(request, 'about.html',context)

#Categories
@login_required
def category(request):
    category_list = Category.objects.all()
    # category_list = {}
    context = {
        'page_title':'Category List',
        'category':category_list,
    }
    return render(request, 'inventory/category.html',context)

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
    return render(request, 'inventory/manage_category.html',context)

@login_required
def save_category(request):
    data = request.POST
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
    return render(request, 'inventory/products.html',context)

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
    
    context = {
        'product' : product,
        'volume_type': volume_type,
        'categories' : categories
    }
    return render(request, 'inventory/manage_product.html',context)

def test(request):
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return render(request, 'test.html',context)

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
        try:
            if id.isnumeric() and int(id) > 0:
                
                Products.objects.filter(id=id).update(
                    code=data['code'],
                    category_id=category,
                    name=str.capitalize(data['name']),
                    #description=data['description'],
                    volume_type = data['volume_type'],
                    measurement_value=data['measurement_value'],
                    #quantity=data['available_quantity'],
                    #buy_price=float(data['buy_price']),
                    min_sell_price=float(data['min_sell_price']),
                    max_sell_price=float(data['max_sell_price']),
                    #status=status
                )
            else:
                new_product = Products(
                    code=data['code'],
                    category_id=category,
                    name=str.capitalize(data['name']),
                    #description=data['description'],
                    volume_type = data['volume_type'],
                    measurement_value=data['measurement_value'],
                    #quantity=data['available_quantity'],
                    #buy_price=float(data['buy_price']),
                    min_sell_price=float(data['min_sell_price']),
                    max_sell_price=float(data['max_sell_price']),
                    #status=1
                )
                new_product.save()

            resp['status'] = 'success'
            messages.success(request, 'Product Successfully saved.')
        except Exception as e:
            logger.error(f"Error saving Product: {e}")
            resp['status'] = 'failed'
            resp['msg'] = 'An error occurred while saving the Product.'

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
        resp['msg'] = 'An error occurred while deleting the Product.'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def pos(request):
    # Ensure URLs are registered only once
    """
    if not hasattr(pos, "_urls_registered"):
        mpesa_client = MpesaClient()
        mpesa_client.register_urls()
        pos._urls_registered = True
    """
    products = Products.objects.filter(status=1)
    context = {
        'page_title': "Point of Sale",
        'products': products,
    }
    return render(request, 'pos/pos.html', context)

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
    return render(request, 'pos/checkout.html', context)

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

@csrf_exempt
@login_required
def save_pos(request):
    resp = {'status': 'failed', 'msg': ''}
    data = request.POST
    
    # Helper function to safely convert input to Decimal
    def safe_decimal(value, default=0):
        try:
            return Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(default)

    try:
        # Convert and validate numeric fields
        payment_method = data.get('payment_method')
        sub_total = safe_decimal(data.get('sub_total', '0'))
        tax = safe_decimal(data.get('tax', '0'))
        tax_amount = safe_decimal(data.get('tax_amount', '0'))
        grand_total = safe_decimal(data.get('grand_total', '0'))
        tendered_amount = grand_total
        amount_change = safe_decimal(data.get('amount_change', '0'))
        cash_amount = safe_decimal(data.get('cash_amount', '0'))
        mpesa_amount = safe_decimal(data.get('mpesa_amount', '0'))
        mpesa_transaction_code = data.get('mpesa_code', '').strip()

        # Validate payment method-specific logic
        if payment_method == 'both':
            if cash_amount <= 0 or mpesa_amount <= 0:
                resp['msg'] = "Both cash and M-Pesa amounts must be greater than zero."
                return JsonResponse(resp)
            if cash_amount + mpesa_amount != grand_total:
                resp['msg'] = "The sum of cash and M-Pesa amounts must equal the grand total."
                return JsonResponse(resp)

        if payment_method == 'mpesa' and not mpesa_transaction_code:
            resp['msg'] = "M-Pesa transaction code is required for M-Pesa payments."
            return JsonResponse(resp)
                    
        # Save the sale record
        sale = Sales(
            code=generate_sale_code(),
            sub_total=sub_total,
            tax=tax,
            tax_amount=tax_amount,
            grand_total=grand_total,
            tendered_amount=tendered_amount,
            amount_change=amount_change,
            payment_method=payment_method,
            cash_amount=cash_amount,
            mpesa_amount=mpesa_amount,
            mpesa_transaction_code=mpesa_transaction_code if payment_method in ['mpesa', 'both'] else '',
            served_by=request.user
        )
        sale.save()

        # Save sales items
        for i, product_id in enumerate(data.getlist('product_id[]')):
            qty = safe_decimal(data.getlist('qty[]')[i])
            price = safe_decimal(data.getlist('price[]')[i])
            product = Products.objects.get(id=product_id)

            # Fetch all non‐empty stock batches for this product, oldest first
            stocks = Stocks.objects.filter(product_id=product, quantity__gt=0).order_by('expiry_date')

            # Total available
            available_qty = sum(stock.quantity for stock in stocks)
            if available_qty < qty:
                raise Exception(f"Insufficient stock for product {product.name}")

            remaining = qty
            for stock in stocks:
                if remaining == 0:
                    break
                use_qty = min(stock.quantity, remaining)
                # Decrement this batch
                stock.quantity -= use_qty
                stock.save()
                # Record the sale item for this batch
                sales_item = salesItems(
                    sale_id=sale,
                    product_id=product,
                    stock_id=stock,
                    qty=use_qty,
                    price=price,
                    total=use_qty * price
                )
                sales_item.save()
                remaining -= use_qty


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
    search_query   = request.GET.get('search', '').strip()
    date_str       = request.GET.get('date', '').strip()  # expects YYYY-MM-DD
    page_number = request.GET.get('page', 1)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    sales = Sales.objects.all().order_by('-date_added')
    
    if payment_method and payment_method in dict(Sales.PaymentMethod.choices):  # Validate filter
        sales = sales.filter(payment_method=payment_method)
    
    # filter by transaction code search
    if search_query:
        sales = sales.filter(code__icontains=search_query)

    # filter by exact date
    if date_str:
        sales = sales.filter(date_added__date=date_str)

    paginator = Paginator(sales, 10)  # Show 10 sales per page
    page_obj = paginator.get_page(page_number)
    sale_data = []
    for sale in page_obj.object_list:
        data = {field.name: getattr(sale, field.name) for field in sale._meta.get_fields(include_parents=False) if field.related_model is None}
        data['items'] = salesItems.objects.filter(sale_id=sale).all()
        data['item_count'] = len(data['items'])
        if 'tax_amount' in data:
            data['tax_amount'] = format(float(data['tax_amount']), '.2f')
        sale_data.append(data)

    context = {
        'sale_data': sale_data,
        'page_obj': page_obj,
        'selected_method': payment_method,        
        'search_query':    search_query,
        'search_date':     date_str,
    }

    if is_ajax:
        html = render_to_string('pos/tables/sales_table.html', context, request=request)
        return JsonResponse({'html': html})

    context.update({
        'page_title': 'Sales Transactions',
        'payment_methods': Sales.PaymentMethod.choices,
    })
    return render(request, 'pos/sales.html', context)

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
    return render(request, 'pos/receipt.html', context)

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
    return render(request, 'inventory/stocks.html', context)

@login_required
def get_stock(request):
    stock_id = request.GET.get('id')    
    try:
        stock = Stocks.objects.get(id=stock_id)
        if stock.supplier_id == None:
            supplier_id = None
        else:
            supplier_id = stock.supplier_id.id
        data = {
            'product_id': stock.product_id.id,
            'supplier_id': supplier_id,
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
    user = get_object_or_404(User, id=request.user.id)
    if user  == None:
        return redirect("posApp:login")
    try:
        if stock_id:
            # Update existing stock
            stock = Stocks.objects.get(id=stock_id)            
            stock.updated_by = user
            if stock.unit_price == 0 and request.POST.get('cost_price') != 0 or request.POST.get('quantity') !=0:
                unit_price =  float(float(request.POST.get('cost_price'))/float(request.POST.get('quantity')))
            else:
                unit_price = stock.unit_price
        else:
            # Create new stock
            stock = Stocks()
            unit_price = float(float(request.POST.get('cost_price'))/float(request.POST.get('quantity')))
            stock.added_by = user
            stock.updated_by = None
        
        if request.POST.get('supplier_id') == '':
            stock.supplier_id = None
        else:
            stock.supplier_id_id = request.POST.get('supplier_id')
        
        expiry_date = request.POST.get('expiry_date') or None
            
        stock.product_id_id = request.POST.get('product_id')       
        stock.batch_number = request.POST.get('batch_number') or ''
        stock.quantity = float(request.POST.get('quantity'))
        stock.unit_price =  unit_price
        stock.cost_price = float(request.POST.get('cost_price'))
        stock.expiry_date = expiry_date or None
        
        stock.save()
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'failed', 'msg': str(e)})

@csrf_exempt
@login_required
def save_unregistered_stock(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'msg': 'Invalid request method'})

    stock_id = request.POST.get('id')
    user = get_object_or_404(User, id=request.user.id)
    if user  == None:
        return redirect("posApp:login")
    try:
        # Validate required fields
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        unit_price = request.POST.get('unit_price')

        if not product_id or not quantity or not unit_price:
            return JsonResponse({'status': 'failed', 'msg': 'Missing required fields'})

        try:
            quantity = float(quantity)
            unit_price = float(unit_price)
        except ValueError:
            return JsonResponse({'status': 'failed', 'msg': 'Invalid quantity or unit price'})

        # Check if updating an existing stock
        if stock_id:
            stock = Stocks.objects.get(id=stock_id)
            stock.updated_by = user
        else:
            stock = Stocks()
            stock.added_by = user
            stock.updated_by = None
            
        if request.POST.get('supplier_id') == '':
            stock.supplier_id = None
        else:
            stock.supplier_id_id = request.POST.get('supplier_id')
            
        # Set stock fields
        stock.product_id_id = product_id
        stock.batch_number = request.POST.get('batch_number') or ''
        stock.quantity = quantity
        stock.unit_price = unit_price
        stock.cost_price = unit_price * quantity  # Calculate cost price
        stock.expiry_date = request.POST.get('expiry_date') or None

        # Save stock
        stock.save()

        return JsonResponse({'status': 'success'})
    except Stocks.DoesNotExist:
        return JsonResponse({'status': 'failed', 'msg': 'Stock not found'})
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
