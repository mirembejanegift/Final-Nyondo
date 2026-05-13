from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, date, timedelta
from .models import Stock
from .models import Sales
from .models import Customer
from .models import Supplier

# # Create your views here.

def landing(request):
    return render(request, 'landing.html')

def login(request):
    return render(request, 'login.html')

def index(request):
    return render(request, 'index.html')

def sing_up(request):
    return render(request, 'sing_up.html')

    




def add(request):
        #Go to the Stock table and fetch all rows.
    stocks = Stock.objects.all()

    return render(request, 'add.html', {'stocks': stocks})



def stock(request):
    if request.method == 'POST':
        # Get the form data
        payload = request.POST
        stock_name = payload.get('product')
        stock_category = payload.get('category')
        stock_quantity = payload.get('quantity')
        stock_cost_price = payload.get('cost_price')
        stock_selling_price = payload.get('selling_price')
        stock_date = payload.get('date')
        stock_specifications = payload.get('specifications')

        
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
    


       


def sales(request):
    if request.method == 'POST':
        payload = request.POST
        sent_stock_id = payload.get('name')
        sales_quantity = payload.get('quantity')
        sales_unit_price = payload.get('unit_price')
        sales_date = payload.get('date')
        sales_customer_name = payload.get('customer_name')
        sales_customer_contact = payload.get('customer_contact')

        stock = Stock.objects.get(id=sent_stock_id)
         
        new_sales = Sales()
        new_sales.name = stock
        new_sales.quantity = sales_quantity
        new_sales.unit_price = sales_unit_price
        new_sales.date = sales_date
        new_sales.customer_name = sales_customer_name        
        new_sales.customer_contact = sales_customer_contact
        new_sales.save()
        return redirect('/save/')

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
    stock = get_object_or_404(Stock, id=id)
    stock.delete()
    return redirect('stock')


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

        return redirect('save')  # make sure this exists

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
        customer_date = payload.get('date')

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
        date = payload.get('date')
        payment_method = payload.get('payment_method')
        amount_paid = payload.get('amount_paid') 
    

        stock = Stock.objects.get(id=stock_id)



        total_cost = quantity * cost_price

        
        if payment_method != 'credit':
            amount_paid = total_cost

        
        new_supply = Supplier()
        new_supply.stock = stock
        new_supply.supplier_name = supplier_name
        new_supply.quantity = quantity
        new_supply.cost_price = cost_price
        new_supply.date = date
        new_supply.payment_method = payment_method
        new_supply.amount_paid = amount_paid
     
        new_supply.save()

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

def edit_supplier(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    stocks = Stock.objects.all()

    if request.method == 'POST':
        supplier.stock = request.POST.get('stock')
        supplier.supplier_name = request.POST.get('supplier_name')
        supplier.quantity = int(request.POST.get('quantity'))
        supplier.cost_price = float(request.POST.get('cost_price'))
        supplier.date = request.POST.get('date')
        supplier.payment_method = request.POST.get('payment_method')
        supplier.amount_paid = request.POST.get('amount_paid')

        supplier.save()

        return redirect('supplier_view')

    return render(request, 'edit_supplier.html', {
        'supplier': supplier,
        'stocks': stocks
    })