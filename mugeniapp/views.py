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
    # this is calling upon the total number of products in stock, 
    total_products = Stock.objects.count()

# this is calculating the total sales amount for the current day by summing up the total_price field of all sales made today.
    today_sales = Sales.objects.all()
    total_sales_amount = sum(sale.total_price for sale in today_sales)


# this is displayin the number of customers on a credit scheme by counting the total number of customer records in the database.
    scheme_customers = Customer.objects.count()

# this is fetching all supplier records to display a list of suppliers who have supplied stock on credit.
    credit_suppliers = Supplier.objects.all()

# this is fetching the 5 most recent sales to display recent activity on the dashboard.
    recent_sales = Sales.objects.order_by('-id')[:5]

# this is fetching all stock items that have a quantity of 5 or less to display low stock alerts on the dashboard. 
    low_stock_products = Stock.objects.filter(quantity__lte=10)

    

    context = {
        'total_products': total_products,
        'total_sales_amount': total_sales_amount,
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
    stock = get_object_or_404(Stock, id=id)
    stock.delete()
    return redirect('add')


@login_required
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
    

# THIS IS THE SALES VIEW. IT HANDLES THE LOGIC FOR RECORDING SALES, INCLUDING VALIDATING INPUT, CALCULATING TOTALS, AND UPDATING STOCK QUANTITIES.
@login_required
@transaction.atomic  # THIS ENSURES THAT ALL DATABASE OPERATIONS WITHIN THIS VIEW ARE ATOMIC, MEANING THEY WILL EITHER ALL SUCCEED OR ALL FAIL TO MAINTAIN DATA INTEGRITY.
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

# VALIDATION: CHECK IF ALL REQUIRED FIELDS ARE PRESENT
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

        if distance <= 10 and total_price <= 500000:
            transport_fee = 0
        else:
            transport_fee = 30000

        grand_total = total_price + transport_fee   #  YOU WERE MISSING THIS

        #  CREATE SALE FIRST
        sale = Sales.objects.create(
            s_name=stock.name,
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
    sale = get_object_or_404(Sales, id=id)  # FIXED: use Sales model
  

    if request.method == 'POST':
        stock = get_object_or_404(Stock, name=sale.name)
        sale.quantity = int(request.POST.get('quantity'))
        sale.unit_price = int(request.POST.get('unit_price'))
        sale.date = request.POST.get('date')
        sale.customer_name = request.POST.get('customer_name')
        sale.customer_contact = request.POST.get('customer_contact')
        sale.distance = float(request.POST.get('distance'))

        # recalculate totals
        sale.total_price = sale.quantity * sale.unit_price

        if sale.distance <= 10 and sale.total_price <= 500000:
            sale.transport_fee = 0
        else:
            sale.transport_fee = 30000

        sale.grand_total = sale.total_price + sale.transport_fee

        sale.save()
        return redirect('save')

    return render(request, 'edit_sale.html', {
        'sale': sale,
        'stock': stock
    })



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

    total_stock_items = Stock.objects.count()
    total_stock_quantity = Stock.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    low_stock_items = Stock.objects.filter(quantity__lt=5)
    out_of_stock = Stock.objects.filter(quantity=0)

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
 