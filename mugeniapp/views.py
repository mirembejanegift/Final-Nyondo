from pyexpat.errors import messages
from turtle import distance

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from datetime import datetime, date, timedelta
from .models import Stock
from django.db import transaction
from .models import Sales
from .models import Customer
from .models import Supplier
from django.db.models import Sum

# # Create your views here.


def index(request):
    return render(request, 'index.html')


#
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # ROLE CHECK (THIS IS THE KEY PART)
            if user.is_superuser or user.groups.filter(name="admin").exists():
                return redirect("dashboard")

            elif user.groups.filter(name="sales").exists():
                return redirect("sales")

            elif user.groups.filter(name="stock_manager").exists():
                return redirect("stock")

            else:
                return redirect("login")

    return render(request, "login.html")



def dashboard(request):

    total_products = Stock.objects.count()

    today_sales = Sales.objects.all()
    total_sales_amount = sum(sale.total_price for sale in today_sales)

    scheme_customers = Customer.objects.count()

    credit_suppliers = Supplier.objects.all()

    recent_sales = Sales.objects.order_by('-id')[:5]

    # ADD THIS (this is what your template needs)
    low_stock_products = Stock.objects.filter(quantity__lte=5)

    context = {
        'total_products': total_products,
        'total_sales_amount': total_sales_amount,
        'scheme_customers': scheme_customers,
        'credit_suppliers': credit_suppliers,
        'recent_sales': recent_sales,

    
        'low_stock_products': low_stock_products,
    }

    return render(request, 'dashboard.html', context)






def stock(request):
    if request.method == 'POST':
        payload = request.POST

        stock_name = payload.get('name')
        stock_category = payload.get('category')
        stock_quantity = payload.get('quantity')
        stock_cost_price = payload.get('cost_price')
        stock_selling_price = payload.get('selling_price')
        stock_date_str = payload.get('date')
        stock_specifications = payload.get('specifications')

   
        try:
            stock_quantity = int(stock_quantity)
        except (TypeError, ValueError):
            return render(request, 'stock.html', {
                'error': 'Quantity must be a valid number'
            })

        if stock_quantity < 0:
            return render(request, 'stock.html', {
                'error': 'Quantity cannot be negative'
            })

    
        try:
            stock_cost_price = float(stock_cost_price)
            stock_selling_price = float(stock_selling_price)
        except (TypeError, ValueError):
            return render(request, 'stock.html', {
                'error': 'Prices must be valid numbers'
            })

   
        try:
            stock_date = datetime.strptime(stock_date_str, "%Y-%m-%d").date()
        except ValueError:
            return render(request, 'stock.html', {
                'error': 'Invalid date format'
            })

        today = date.today()
        one_week_ago = today - timedelta(days=7)

        if stock_date > today:
            return render(request, 'stock.html', {
                'error': 'Date cannot be in the future'
            })
        elif stock_date < one_week_ago:
            return render(request, 'stock.html', {
                'error': 'Date cannot be older than 1 week'
            })

   
        new_stock = Stock(
            name=stock_name,
            category=stock_category,
            quantity=stock_quantity,
            cost_price=stock_cost_price,
            selling_price=stock_selling_price,
            date=stock_date,
            specifications=stock_specifications
        )
        new_stock.save()

        return redirect('/add/')

    return render(request, 'stock.html')


    

def add(request):
    stocks = Stock.objects.all()

    return render(request, 'add.html', {'stocks': stocks})



def delete_stock(request, id):
    stock = get_object_or_404(Stock, id=id)
    stock.delete()
    return redirect('add')



def edit_stock(request, id):
    stock = get_object_or_404(Stock, id=id)
    stocks = Stock.objects.all()



    if request.method == 'POST':
        stock.name = request.POST.get('name')
        stock.category = request.POST.get('category')
        stock.quantity = request.POST.get('quantity')
        stock.cost_price = request.POST.get('cost_price')
        stock.selling_price = request.POST.get('selling_price')
        stock.date = request.POST.get('date')
        stock.specifications = request.POST.get('specifications')
        stock.save()
        return redirect('add')

    return render(request, 'edit_stock.html', {
        'stock': stock,
        'stocks': stocks
    })
    






@transaction.atomic
def sales(request):

    if request.method == 'POST':

        payload = request.POST

        stock_id = payload.get('stock_id')
        quantity = payload.get('quantity')
        unit_price = payload.get('unit_price')
        date_str = payload.get('date')
        customer_name = payload.get('customer_name')
        customer_contact = payload.get('customer_contact')
        distance = payload.get('distance')

        if not all([stock_id, quantity, unit_price, date_str, customer_name, customer_contact, distance]):
            messages.error(request, "All fields are required.")
            return redirect('sales')

        try:
            quantity = int(quantity)
            unit_price = int(unit_price)
            distance = float(distance)
        except ValueError:
            messages.error(request, "Invalid numeric values entered.")
            return redirect('sales')

        stock = get_object_or_404(Stock, id=stock_id)

        if quantity > stock.quantity:
            messages.error(request, f"Only {stock.quantity} items available in stock.")
            return redirect('sales')

        # calculate totals
        total_price = quantity * unit_price

        if distance <= 10 and total_price >= 500000:
            transport_fee = 0
        else:
            transport_fee = 30000

        grand_total = total_price + transport_fee   #  YOU WERE MISSING THIS

        #  CREATE SALE FIRST
        sale = Sales.objects.create(
            name=stock,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            distance=distance,
            transport_fee=transport_fee,
            grand_total=grand_total,
            date=date_str,
            customer_name=customer_name,
            customer_contact=customer_contact
        )

        #  THEN REDUCE STOCK SAFELY
        stock.quantity -= quantity
        stock.save()

        messages.success(request, "Sale recorded successfully.")
        return redirect('save')

    stocks = Stock.objects.all()
    return render(request, 'sales.html', {'stocks': stocks})






def save(request):
    sales = Sales.objects.all()

    return render(request, 'save.html', {'sales': sales})





def sales_receipt(request, id):
    sale = get_object_or_404(Sales, id=id)
    return render(request, 'sale_receipt.html', {'sale': sale})







def delete_sale(request, id):
    sale = get_object_or_404(Sales, id=id)   # FIXED: use Sales model
    sale.delete()
    return redirect('save')





def edit_sale(request, id):
    sale = get_object_or_404(Sales, id=id)
    stocks = Stock.objects.all()

    if request.method == 'POST':
        sale.name_id = request.POST.get('name')
        sale.quantity = int(request.POST.get('quantity'))
        sale.unit_price = int(request.POST.get('unit_price'))
        sale.date = request.POST.get('date')
        sale.customer_name = request.POST.get('customer_name')
        sale.customer_contact = request.POST.get('customer_contact')

        sale.save()

        return redirect('save')  

    return render(request, 'edit_sale.html', {
        'sale': sale,
        'stocks': stocks
    })







def customer(request):

    today = datetime.today().date()
    one_week_ago = today - timedelta(days=7)

    if request.method == "POST":

        name = request.POST.get("name")
        nin = request.POST.get("nin")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        product = request.POST.get("product")
        amount = request.POST.get("amount")
        date = request.POST.get("date")

        if not all([name, nin, email, contact, product, amount, date]):
            messages.error(request, "All fields are required.")
            return redirect("customer_list")

   
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, "Amount must be a valid number.")
            return redirect("customer_list")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero (no negatives allowed).")
            return redirect("customer_list")

        if not contact.isdigit():
            messages.error(request, "Contact must contain only numbers.")
            return redirect("customer_list")

        if len(contact) != 10:
            messages.error(request, "Contact must be exactly 10 digits.")
            return redirect("customer_list")

    
        try:
            date_value = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("customer_list")

        if date_value > today:
            messages.error(request, "Date cannot be in the future.")
            return redirect("customer_list")

        if date_value < one_week_ago:
            messages.error(request, "Date cannot be older than 1 week.")
            return redirect("customer_list")

   
        Customer.objects.create(
            name=name,
            nin=nin,
            email=email,
            contact=contact,
            product=product,
            amount=amount,
            date=date_value
        )

        messages.success(request, "Customer saved successfully.")
        return redirect("customer_list")

    return render(request, "customer.html", {
        "today": today,
        "one_week_ago": one_week_ago
    })






def customer_list(request):
    if request.method == 'POST':
        payload = request.POST

        customer_name = payload.get('name')
        customer_nin = payload.get('nin')
        customer_email = payload.get('email')
        customer_contact = payload.get('contact')
        customer_product = payload.get('product')

        
        customer_amount = int(payload.get('amount'))

        customer_date_str = payload.get('date')

        if customer_amount < 0:
            messages.error(request, "Amount cannot be negative.")
            return redirect('customer_list')

        customer_date = datetime.strptime(customer_date_str, "%Y-%m-%d").date()

        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

  
        if customer_date < one_week_ago or customer_date > today:
            messages.error(request, "Date must be within the past week and not in the future.")
            return redirect('customer_list')

        # Save customer
        new_customer = Customer(
            name=customer_name,
            nin=customer_nin,
            email=customer_email,
            contact=customer_contact,
            product=customer_product,
            amount=customer_amount,
            date=customer_date
        )

        new_customer.save()

        messages.success(request, "Customer added successfully.")

        return redirect('customer')

    return render(request, 'customer_list.html')





def customer_receipt(request, id):
    customer = get_object_or_404(Customer, id=id)
    return render(request, 'customer_receipt.html', {'customer': customer})



def customer(request):
    customers = Customer.objects.all()
    return render(request, 'customer.html', {'customers': customers})



def delete_customer(request, id):
    customer = Customer.objects.get(id=id)
    customer.delete()
    return redirect('customer')




def edit_customer(request, id):
    customer = get_object_or_404(Customer, id=id)
    customers = Customer.objects.all()

    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.nin = request.POST.get('nin')
        customer.email = request.POST.get('email')
        customer.contact = request.POST.get('contact')
        customer.product = request.POST.get('product')
        customer.amount = request.POST.get('amount')
        customer.date = request.POST.get('date')
        customer.save()
        return redirect('customer')

    return render(request, 'edit_customer_list.html', {
        'customer': customer,
        'customers': customers
    })





from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Stock, Supplier


def supplier(request):

    stocks = Stock.objects.all()

    if request.method == 'POST':

        payload = request.POST

        stock_id = payload.get('stock')
        supplier_name = payload.get('supplier_name')
        supplier_contact = payload.get('supplier_contact')

        quantity = payload.get('quantity')
        cost_price = payload.get('cost_price')

        amount_paid = payload.get('amount_paid') or 0

        supplier_date_str = payload.get('date')
        method_of_payment = payload.get('method_of_payment')

        # REQUIRED FIELDS

        if not all([
            stock_id,
            supplier_name,
            supplier_contact,
            quantity,
            cost_price,
            supplier_date_str,
            method_of_payment
        ]):
            messages.error(request, "All fields are required.")
            return redirect('supplier')

        # QUANTITY VALIDATION

        try:
            quantity = int(quantity)

        except ValueError:
            messages.error(request, "Quantity must be a valid number.")
            return redirect('supplier')

        if quantity <= 0:
            messages.error(request, "Quantity must be greater than zero.")
            return redirect('supplier')

        # COST PRICE VALIDATION

        try:
            cost_price = float(cost_price)

        except ValueError:
            messages.error(request, "Cost price must be a valid number.")
            return redirect('supplier')

        if cost_price <= 0:
            messages.error(request, "Cost price must be greater than zero.")
            return redirect('supplier')

        # AMOUNT PAID VALIDATION

        try:
            amount_paid = float(amount_paid)

        except ValueError:
            messages.error(request, "Amount paid must be a valid number.")
            return redirect('supplier')

        if amount_paid < 0:
            messages.error(request, "Amount paid cannot be negative.")
            return redirect('supplier')

        # DATE VALIDATION

        try:
            supplier_date = datetime.strptime(
                supplier_date_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('supplier')

        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

        if supplier_date < one_week_ago or supplier_date > today:
            messages.error(
                request,
                "Date must be within the past week and not in the future."
            )
            return redirect('supplier')

        # GET STOCK

        try:
            stock = Stock.objects.get(id=stock_id)

        except Stock.DoesNotExist:
            messages.error(request, "Selected stock does not exist.")
            return redirect('supplier')

        # CALCULATIONS

        total_cost = quantity * cost_price

        # IF CASH => FULLY PAID

        if method_of_payment == 'cash':
            amount_paid = total_cost
            balance = 0

        else:
            balance = total_cost - amount_paid

        # PREVENT OVERPAYMENT

        if amount_paid > total_cost:
            messages.error(
                request,
                "Amount paid cannot be greater than total cost."
            )
            return redirect('supplier')

        # SAVE SUPPLIER

        new_supplier = Supplier(
            stock=stock,
            supplier_name=supplier_name,
            supplier_contact=supplier_contact,
            quantity=quantity,
            cost_price=cost_price,
            total_cost=total_cost,
            amount_paid=amount_paid,
            balance=balance,
            date=supplier_date,
            method_of_payment=method_of_payment
        )

        new_supplier.save()

        # UPDATE STOCK

        stock.quantity += quantity
        stock.save()

        messages.success(
            request,
            "Supplier record added successfully."
        )

        return redirect('supplier_view')

    return render(request, 'supplier.html', {
        'stocks': stocks
    })





def supplier_view(request):
    supplies = Supplier.objects.all()
    return render(request, 'supplier_view.html', {'supplies': supplies})

def delete_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    return redirect('supplier_view')



def edit_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    stocks = Stock.objects.all()

    if request.method == 'POST':
        stock_id = request.POST.get('stock')
        supplier.stock = get_object_or_404(Stock, id=stock_id)  # FIXED

        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.quantity = int(request.POST.get('quantity'))
        supplier.cost_price = float(request.POST.get('cost_price'))
        supplier.date = request.POST.get('date')
        supplier.method_of_payment = request.POST.get('method_of_payment')  # FIXED (removed space)
        supplier.amount_paid = request.POST.get('amount_paid')

        supplier.save()
        return redirect('supplier_view')

    return render(request, 'edit_supplier.html', {
        'supplier': supplier,
        'stocks': stocks
    })


def supplier_receipt(request, id):
    supplier = get_object_or_404(Supplier, id=id)

    total_cost = supplier.quantity * supplier.cost_price
    balance = total_cost - supplier.amount_paid

    if balance < 0:
        balance = 0

    context = {
        "supplier": supplier,
        "total_cost": total_cost,
        "balance": balance,
    }

    return render(request, "supplier_receipt.html", context)  
def reports(request):

    # STOCK SUMMARY
    total_stock_items = Stock.objects.count()
    total_stock_quantity = Stock.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    low_stock_items = Stock.objects.filter(quantity__lt=5)
    out_of_stock = Stock.objects.filter(quantity=0)

    # CUSTOMER SUMMARY
    total_customers = Customer.objects.count()
    total_sales = Customer.objects.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # SUPPLIER SUMMARY
    total_suppliers = Supplier.objects.count()

    context = {
        "total_stock_items": total_stock_items,
        "total_stock_quantity": total_stock_quantity,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,

        "total_customers": total_customers,
        "total_sales": total_sales,

        "total_suppliers": total_suppliers,
    }

    return render(request, "reports.html", context)
 