from pyexpat.errors import messages

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from datetime import datetime, date, timedelta
from .models import Stock
from .models import Sales
from .models import Customer
from .models import Supplier

# # Create your views here.


def index(request):
    return render(request, 'index.html')



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

    total_sales_amount = 0

    credit_customers = Customer.objects.filter(method_of_payment="Credit").count()

    low_stock_products = Stock.objects.filter(quantity__lt=10)

    low_stock = low_stock_products.count()

    recent_sales = Sales.objects.order_by('-id')[:5]

    context = {
        'total_products': total_products,
        'today_sales': total_sales_amount,
        'credit_customers': credit_customers,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'dashboard.html', context)




def stock(request):
    if request.method == 'POST':
        payload = request.POST

        stock_name = payload.get('product')
        stock_category = payload.get('category')
        stock_quantity = payload.get('quantity')
        stock_cost_price = payload.get('cost_price')
        stock_selling_price = payload.get('selling_price')
        stock_date_str = payload.get('date')
        stock_specifications = payload.get('specifications')

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

        new_stock = Stock()
        new_stock.name = stock_name
        new_stock.category = stock_category
        new_stock.quantity = stock_quantity
        new_stock.cost_price = stock_cost_price
        new_stock.selling_price = stock_selling_price
        new_stock.date = stock_date
        new_stock.specifications = stock_specifications     
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
        stock.name = request.POST.get('product')
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
    




from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from datetime import datetime, timedelta

from .models import Stock, Sales


def sales(request):

    if request.method == 'POST':

        payload = request.POST


        stock_id = payload.get('name')
        quantity = payload.get('quantity')
        unit_price = payload.get('unit_price')
        date_str = payload.get('date')
        customer_name = payload.get('customer_name')
        customer_contact = payload.get('customer_contact')
        distance = payload.get('distance')

      
        if not all([stock_id, quantity, unit_price, date_str, customer_name, customer_contact, distance]):
            messages.error(request, "All fields are required.")
            return redirect('sales')

        
        if not customer_contact.isdigit() or len(customer_contact) != 10:
            messages.error(request, "Customer contact must be exactly 10 digits.")
            return redirect('sales')

      
        try:
            quantity = int(quantity)
            unit_price = float(unit_price)
            distance = float(distance)
        except ValueError:
            messages.error(request, "Invalid numeric values entered.")
            return redirect('sales')

        # Prevent nonsense input
        if quantity <= 0:
            messages.error(request, "Quantity must be greater than zero.")
            return redirect('sales')

   
        try:
            sales_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('sales')

        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

        if sales_date < one_week_ago or sales_date > today:
            messages.error(request, "Date must be within the past week and not in the future.")
            return redirect('sales')

        stock = get_object_or_404(Stock, id=stock_id)

      
        if quantity > stock.quantity:
            messages.error(request, f"Only {stock.quantity} items available in stock.")
            return redirect('sales')

        total_price = quantity * unit_price

        # Transport logic
        if total_price >= 500000 and distance <= 10:
            transport_fee = 0
        else:
            transport_fee = 30000

        grand_total = total_price + transport_fee

        new_sale = Sales.objects.create(
            name=stock,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            distance=distance,
            transport_fee=transport_fee,
            grand_total=grand_total,
            date=sales_date,
            customer_name=customer_name,
            customer_contact=customer_contact
        )

      
        stock.quantity -= quantity
        stock.save()

        messages.success(request, "Sale recorded successfully.")

        return redirect('save')

   
    stocks = Stock.objects.all()

    return render(request, 'sales.html', {'stocks': stocks})



  
def sales_receipt(request,id):

    sale = get_object_or_404(Sales, id=id)
    stocks = Stock.objects.all() 

    if request.method == 'POST':
        sale.name_id = request.POST.get('name')
        sale.quantity = (request.POST.get('quantity'))
        sale.unit_price = request.POST.get('unit_price')
        sale.date = request.POST.get('date')
        sale.customer_name = request.POST.get('customer_name')
        sale.customer_contact = request.POST.get('customer_contact')

        sale.save()
        return redirect('save',)

    return render(request, 'sales_receipt.html', {
        'sale': sale,
        'stocks': stocks  
    })



def save(request):
    sales = Sales.objects.all()

    return render(request, 'save.html', {'sales': sales})


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


def customer_list(request):
    if request.method == 'POST':
        payload = request.POST
        customer_name = payload.get('name')
        customer_nin = payload.get('nin')
        customer_email = payload.get('email')
        customer_contact = payload.get('contact')
        customer_product = payload.get('product')
        customer_amount = payload.get('amount')
        customer_date_str = payload.get('date')

        customer_date = datetime.strptime(customer_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

        if customer_date < one_week_ago or customer_date > today:
            messages.error(request, "Date must be within the past week and not in the future.")
            return redirect('customer_list')
       

        new_customer = Customer()
        new_customer.name = customer_name
        new_customer.nin = customer_nin
        new_customer.email = customer_email
        new_customer.contact = customer_contact
        new_customer.product = customer_product
        new_customer.amount = customer_amount
        new_customer.date = customer_date
        new_customer.save()

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


def supplier(request):
    stocks = Stock.objects.all()

    if request.method == 'POST':
        payload = request.POST

        stock_id = payload.get('stock')
        supplier_name = payload.get('supplier_name')
        quantity = int(payload.get('quantity'))
        cost_price = float(payload.get('cost_price'))
        supplier_date_str = payload.get('date')   # comes in as string
        method_of_payment = payload.get('method_of_payment')

        # Convert string to date object
        supplier_date = datetime.strptime(supplier_date_str, "%Y-%m-%d").date()
        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

        if supplier_date < one_week_ago or supplier_date > today:
            messages.error(request, "Date must be within the past week and not in the future.")
            return redirect('supplier')

        stock = Stock.objects.get(id=stock_id)
        new_supplier = Supplier(
            stock=stock,
            supplier_name=supplier_name,
            quantity=quantity,
            cost_price=cost_price,
            date=supplier_date,
            method_of_payment=method_of_payment
        )
        new_supplier.save()

        stock.quantity += quantity
        stock.save()

        return redirect('supplier_view')

    return render(request, 'supplier.html', {'stocks': stocks})







def supplier_view(request):
    supplies = Supplier.objects.all()
    return render(request, 'supplier_view.html', {'supplies': supplies})

def delete_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    return redirect('supplier_view')

from django.shortcuts import get_object_or_404

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