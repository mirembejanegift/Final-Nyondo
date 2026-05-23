from os import name
from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, date, timedelta
from .models import Stock
from django.db import transaction
from .models import Sales
from .models import Customer
from .models import Supplier
from django.db.models import Sum
from django.utils.timezone import now
from django.shortcuts import render
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta


from .models import Stock, Sales, Customer, Supplier


def dashboard(request):

    # TOTAL PRODUCTS IN STOCK
    total_products = Stock.objects.count()

    # TODAY'S SALES (ONLY TODAY)
    today = now().date()

    today_sales_qs = Sales.objects.filter(date=today)

    total_sales_amount = today_sales_qs.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # CUSTOMERS
    scheme_customers = Customer.objects.count()

    # SUPPLIERS
    credit_suppliers = Supplier.objects.all()

    # RECENT SALES
    recent_sales = Sales.objects.order_by('-id')[:5]

    # LOW STOCK ALERT
    low_stock_products = Stock.objects.filter(quantity__lte=10)

    context = {
        'total_products': total_products,
        'today_sales_amount': total_sales_amount,
        'scheme_customers': scheme_customers,
        'credit_suppliers': credit_suppliers,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'dashboard.html', context)


# # Create your views here.
# THIS IS THE HOME PAGE VIEW
def index(request):
    return render(request, 'index.html')



# THIS IS THE LOGIN VIEW. I USED DJANGO'S BUILT-IN AUTHENTICATION SYSTEM TO HANDLE USER LOGIN.
# i used a supperuser check for admin role and group checks for sales and stock manager roles. 
def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if user.is_superuser or user.groups.filter(name="admin").exists():
                return redirect("dashboard")

            elif user.groups.filter(name="sales").exists():
                return redirect("sales")

            elif user.groups.filter(name="stock_manager").exists():
                return redirect("stock")

            else:
                return redirect("login")


    return render(request, "login.html")



def logout_view(request):
    logout(request)
    return redirect('login')

# THIS IS THE DASHBOARD VIEW. IT DISPLAYS KEY METRICS AND RECENT ACTIVITY TO GIVE THE ADMIN A QUICK OVERVIEW OF THE SYSTEM'S STATUS.

@login_required



def dashboard(request):

    # TOTAL PRODUCTS IN STOCK
    total_products = Stock.objects.count()

    # TODAY'S SALES (ONLY TODAY)
    today = now().date()

    today_sales_qs = Sales.objects.filter(date=today)

    total_sales_amount = today_sales_qs.aggregate(
        total=Sum('total_price')
    )['total'] or 0

    # CUSTOMERS
    scheme_customers = Customer.objects.count()

    # SUPPLIERS
    credit_suppliers = Supplier.objects.all()

    # RECENT SALES
    recent_sales = Sales.objects.order_by('-id')[:5]

    # LOW STOCK ALERT
    low_stock_products = Stock.objects.filter(quantity__lte=10)

    context = {
        'total_products': total_products,
        'today_sales_amount': total_sales_amount,
        'scheme_customers': scheme_customers,
        'credit_suppliers': credit_suppliers,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'dashboard.html', context)




# THIS IS THE STOCK VIEW. IT HANDLES THE LOGIC FOR ADDING NEW STOCK ITEMS, INCLUDING VALIDATING INPUT AND SAVING STOCK RECORDS TO THE DATABASE.


@login_required    
def stock(request):
    if request.method == 'POST':

        payload = request.POST

        stock_name = payload.get('name')
        stock_category = payload.get('category')
        stock_quantity = payload.get('quantity')
        stock_supplier = payload.get('supplier')
        stock_cost_price = payload.get('cost_price')
        stock_selling_price = payload.get('selling_price')
        stock_date_str = payload.get('date')
        stock_specifications = payload.get('specifications') 
        

        
        try:
            stock_quantity = int(stock_quantity)
            if stock_quantity <= 0:
                return render(request, 'stock.html', {'error': 'Quantity must be greater than 0'})
        except (TypeError, ValueError):
            return render(request, 'stock.html', {'error': 'Quantity must be a valid number'})

        try:
            stock_cost_price = float(stock_cost_price)
            stock_selling_price = float(stock_selling_price)
            if stock_cost_price <= 0 or stock_selling_price <= 0:
                return render(request, 'stock.html', {'error': 'Prices must be greater than 0'})
        except (TypeError, ValueError):
            return render(request, 'stock.html', {'error': 'Prices must be valid numbers'})

        try:
            stock_date = datetime.strptime(stock_date_str, "%Y-%m-%d").date()
        except ValueError:
            return render(request, 'stock.html', {'error': 'Invalid date format'})

        today = date.today()
        one_week_ago = today - timedelta(days=7)

        if stock_date > today:
            return render(request, 'stock.html', {'error': 'Date cannot be in the future'})
        if stock_date < one_week_ago:
            return render(request, 'stock.html', {'error': 'Date cannot be older than 1 week'})

    
        stock_name = stock_name.strip().title()

   
        stock_obj, created = Stock.objects.get_or_create(
            name=stock_name,
            defaults={
                'category': stock_category,
                'quantity': 0,
                'cost_price': stock_cost_price,
                'selling_price': stock_selling_price,
                'date': stock_date,
                'specifications': stock_specifications
            }
        )

        stock_obj.quantity = (stock_obj.quantity or 0) + stock_quantity
        stock_obj.save()

        return redirect('/add/')

    return render(request, 'stock.html')



@login_required
def add(request):
    stocks = Stock.objects.all()

    return render(request, 'add.html', {'stocks': stocks})


@login_required
def delete_stock(request, id):
     if request.user.is_superuser:
        stock = get_object_or_404(Stock, id=id)
        stock.delete()
        return redirect('add')
     else:
        messages.error(request, "You are not authorized to delete this stock.")
        return redirect('add')


@login_required
def edit_stock(request, id):
 if request.user.is_superuser:
    stock = get_object_or_404(Stock, id=id)

    if request.method == 'POST':

        name = request.POST.get('name')
        category = request.POST.get('category')
        quantity = request.POST.get('quantity')
        supplier = request.POST.get('supplier')
        cost_price = request.POST.get('cost_price')
        selling_price = request.POST.get('selling_price')
        date = request.POST.get('date')

        errors = []

        if not name:
            errors.append("Product name is required")

        if not quantity or int(quantity) < 0:
            errors.append("Quantity must be 0 or more")

        if not cost_price or int(cost_price) < 0:
            errors.append("Cost price must be valid")

        if not selling_price or int(selling_price) < 0:
            errors.append("Selling price must be valid")

        if not supplier:
            errors.append("Supplier is required")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'edit_stock.html', {'stock': stock})

        stock.name = name
        stock.category = category
        stock.quantity = quantity
        stock.cost_price = cost_price
        stock.selling_price = selling_price
        stock.date = date
        stock.specifications = request.POST.get('specifications')
        stock.payment = request.POST.get('payment')
        stock.supplier = request.POST.get('supplier')

        stock.save()

        messages.success(request, "Stock updated successfully")
        return redirect('add')

    return render(request, 'edit_stock.html', {'stock': stock})


    

# THIS IS THE SALES VIEW. IT HANDLES THE LOGIC FOR RECORDING SALES, INCLUDING VALIDATING INPUT, CALCULATING TOTALS, AND UPDATING STOCK QUANTITIES.
@login_required
@transaction.atomic  # THIS ENSURES THAT ALL DATABASE OPERATIONS WITHIN THIS VIEW ARE ATOMIC, MEANING THEY WILL EITHER ALL SUCCEED OR ALL FAIL TO MAINTAIN DATA INTEGRITY.
def sales(request):

    if request.method == 'POST':

        payload = request.POST

        stock_id = payload.get('stock_id')
        quantity = payload.get('quantity')
        date_str = payload.get('date')
        customer_name = payload.get('customer_name')
        customer_contact = payload.get('customer_contact')
        distance = payload.get('distance')

        # VALIDATION: required fields (NO unit_price anymore)
        if not all([stock_id, quantity, date_str, customer_name, customer_contact, distance]):
            messages.error(request, "All fields are required.")
            return redirect('sales')

        # Convert numeric values safely
        try:
            quantity = int(quantity)
            distance = float(distance)
        except ValueError:
            messages.error(request, "Invalid numeric values entered.")
            return redirect('sales')

        # Get stock object
        stock = get_object_or_404(Stock, id=stock_id)

        # AUTO PRICE (NO USER INPUT)
        unit_price = stock.selling_price

        # Check stock availability
        if quantity > stock.quantity:
            messages.error(request, f"Only {stock.quantity} items available in stock.")
            return redirect('sales')

        # CALCULATIONS
        total_price = quantity * unit_price

        if distance <= 10 and total_price <= 500000:
            transport_fee = 0
        else:
            transport_fee = 30000

        grand_total = total_price + transport_fee

        # CREATE SALE (FIXED FIELD NAME)
        Sales.objects.create(
            name=stock,   # FIXED FK FIELD

            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,

            distance=distance,
            transport_fee=transport_fee,
            grand_total=grand_total,

            date=datetime.strptime(date_str, "%Y-%m-%d").date(),

            customer_name=customer_name,
            customer_contact=customer_contact
        )

        # REDUCE STOCK
        stock.quantity -= quantity
        stock.save()

        messages.success(request, "Sale recorded successfully.")
        return redirect('save')

    stocks = Stock.objects.all()
    return render(request, 'sales.html', {'stocks': stocks})





@login_required
def save(request):
    sales = Sales.objects.all()

    return render(request, 'save.html', {'sales': sales})



@login_required
def sales_receipt(request, id):
    sale = get_object_or_404(Sales, id=id)
    return render(request, 'sales_receipt.html', {'sale': sale})




@login_required
def delete_sale(request, id):
    if request.user.is_superuser:
        sale = get_object_or_404(Sales, id=id)   # FIXED: use Sales model
        sale.delete()
    return redirect('save')



@login_required
def edit_sale(request, id):
    if not request.user.is_superuser:
        return redirect('sales_list')

    sale = get_object_or_404(Sales, id=id)

    if request.method == 'POST':

        name = request.POST.get('name')
        quantity = request.POST.get('quantity')
        distance = request.POST.get('distance')
        unit_price = request.POST.get('unit_price')
        date = request.POST.get('date')
        customer_name = request.POST.get('customer_name')
        customer_contact = request.POST.get('customer_contact')

        errors = []

        if not name:
            errors.append("Sale name is required")

        if not quantity or int(quantity) < 0:
            errors.append("Quantity must be 0 or more")

        if not unit_price or int(unit_price) < 0:
            errors.append("Unit price must be valid")

        if not date:
            errors.append("Date is required")

        if not customer_name:
            errors.append("Customer name is required")

        if not customer_contact:
            errors.append("Customer contact is required")


        if distance and float(distance) < 0:
            errors.append("Distance cannot be negative")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'edit_sale.html', {'sale': sale})

        sale.name = name
        sale.quantity = quantity
        sale.distance = distance
        sale.unit_price = unit_price
        sale.date = date
        sale.customer_name = customer_name
        sale.customer_contact = customer_contact

        sale.save()

        messages.success(request, "Sale updated successfully")
        return redirect('sales_list')

    return render(request, 'edit_sale.html', {'sale': sale})



# THIS IS THE CUSTOMER VIEW. IT HANDLES THE LOGIC FOR ADDING CUSTOMERS, INCLUDING VALIDATING INPUT AND SAVING CUSTOMER RECORDS TO THE DATABASE.
@login_required
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

        # CHECK EMPTY FIELDS
        if not all([name, nin, email, contact, product, amount, date]):
            messages.error(request, "All fields are required.")
            return redirect("customer")

        # VALIDATE AMOUNT
        try:
            amount = float(amount)
        except ValueError:
            messages.error(request, "Amount must be a valid number.")
            return redirect("customer")

        if amount <= 0:
            messages.error(request, "Amount must be greater than zero.")
            return redirect("customer")

        # VALIDATE CONTACT
        if not contact.isdigit():
            messages.error(request, "Contact must contain only numbers.")
            return redirect("customer")

        if len(contact) != 10:
            messages.error(request, "Contact must be exactly 10 digits.")
            return redirect("customer")

        # VALIDATE DATE
        try:
            date_value = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("customer")

        if date_value > today:
            messages.error(request, "Date cannot be in the future.")
            return redirect("customer")

        if date_value < one_week_ago:
            messages.error(request, "Date cannot be older than 1 week.")
            return redirect("customer")

        # CHECK IF CUSTOMER ALREADY EXISTS
        customer, created = Customer.objects.get_or_create(
            nin=nin,
            defaults={
                'name': name,
                'email': email,
                'contact': contact,
                'product': product,
                'amount': amount,
                'date': date_value
            }
        )

        # IF CUSTOMER EXISTS, ADD NEW DEPOSIT
        if not created:
            customer.amount += amount
            customer.name = name
            customer.email = email
            customer.contact = contact
            customer.product = product
            customer.date = date_value
            customer.save()

            messages.success(request, "Deposit added successfully.")

        else:
            messages.success(request, "Customer saved successfully.")

        return redirect("customer_list")

    return render(request, "customer.html", {
        "today": today,
        "one_week_ago": one_week_ago
    })


# CUSTOMER LIST VIEW
# Displays all customers
@login_required
def customer_list(request):

    customers = Customer.objects.all().order_by('-id')

    return render(request, "customer_list.html", {
        "customers": customers
    })



# THIS IS THE CUSTOMER LIST VIEW. IT DISPLAYS A LIST OF ALL CUSTOMERS IN THE DATABASE AND PROVIDES OPTIONS TO EDIT OR DELETE CUSTOMER RECORDS.

@login_required
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




@login_required
def customer_receipt(request, id):
    customer = get_object_or_404(Customer, id=id)
    return render(request, 'customer_receipt.html', {'customer': customer})



@login_required
def customer(request):
    customers = Customer.objects.all()
    return render(request, 'customer.html', {'customers': customers})


@login_required
def delete_customer(request, id):
    customer = Customer.objects.get(id=id)
    customer.delete()
    return redirect('customer')



@login_required
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



        if len( customer.nin) != 14:
         messages.error(request, "NIN must be exactly 14 characters.")
   
        else:
            messages.success(request, "Customer updated successfully.")

        if customer.contact :
            if not customer.contact.isdigit():
                messages.error(request, "Contact must contain only numbers.")
            elif len(customer.contact) != 10:
                messages.error(request, "Contact must be exactly 10 digits.")
            else:
                messages.success(request, "Customer updated successfully.")

    return render(request, 'edit_customer_list.html', {
        'customer': customer,
        'customers': customers
    })


# THIS IS THE SUPPLIER VIEW. IT HANDLES THE LOGIC FOR ADDING SUPPLIERS, INCLUDING VALIDATING INPUT AND SAVING SUPPLIER RECORDS TO THE DATABASE.
@login_required
def supplier(request):

    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('index')

    if request.method == 'POST':

        payload = request.POST

        product_name = payload.get('product_name')
        supplier_name = payload.get('supplier_name')
        supplier_contact = payload.get('supplier_contact')

        quantity = payload.get('quantity')
        cost_price = payload.get('cost_price')

        amount_paid = payload.get('amount_paid') or 0
        supplier_date_str = payload.get('date')
        method_of_payment = payload.get('method_of_payment')

        # VALIDATION
        if not all([product_name, supplier_name, quantity, cost_price, supplier_date_str, method_of_payment]):
            messages.error(request, "All fields are required.")
            return redirect('supplier')

        try:
            quantity = int(quantity)
            cost_price = float(cost_price)
            amount_paid = float(amount_paid)
        except ValueError:
            messages.error(request, "Invalid number input.")
            return redirect('supplier')

        if quantity <= 0 or cost_price <= 0:
            messages.error(request, "Quantity and cost price must be greater than 0.")
            return redirect('supplier')

        # DATE
        try:
            supplier_date = datetime.strptime(supplier_date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date.")
            return redirect('supplier')

        total_cost = quantity * cost_price

        if method_of_payment == 'cash':
            amount_paid = total_cost
            balance = 0
        else:
            balance = total_cost - amount_paid

        if amount_paid > total_cost:
            messages.error(request, "Overpayment is not allowed.")
            return redirect('supplier')

        # SAVE SUPPLIER
        Supplier.objects.create(
            product_name=product_name,
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

      
        stock, created = Stock.objects.get_or_create(
            name=name,
            defaults={
                "quantity": 0,
                "cost_price": cost_price,
                "selling_price": 0,
                "date": supplier_date
            }
        )

        stock.quantity += quantity
        stock.cost_price = cost_price
        stock.save()

        messages.success(request, "Supplier added and stock updated successfully.")
        return redirect('supplier_view')

    return render(request, 'supplier.html')

@login_required
def supplier_view(request):
    supplies = Supplier.objects.all()
    return render(request, 'supplier_view.html', {'supplies': supplies})

@login_required
def delete_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    return redirect('supplier_view')


@login_required
def edit_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
  

    if request.method == 'POST':
        supplier.product_name = request.POST.get('product_name')
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
      
    })

@login_required
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


@login_required




def reports(request):

    return render(request, 'reports.html',)