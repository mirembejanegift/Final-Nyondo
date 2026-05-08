from django.shortcuts import render, redirect, get_object_or_404
import datetime
from .models import Stock
from .models import Sales
from .models import Customer

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
        stock_supplier = payload.get('supplier')
        stock_specifications = payload.get('specifications')

        
        new_stock = Stock()
        new_stock.name = stock_name
        new_stock.category = stock_category
        new_stock.quantity = stock_quantity
        new_stock.cost_price = stock_cost_price
        new_stock.selling_price = stock_selling_price
        new_stock.date = stock_date
        new_stock.supplier = stock_supplier
        new_stock.specifications = stock_specifications
        new_stock.save()
        return redirect('/add/')

    return render(request, 'stock.html')


def delete_stock(request, id):
    stock = Stock.objects.get(id=id)
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
        stock.supplier = request.POST.get('supplier')
        stock.specifications = request.POST.get('specifications')
        stock.save()
        return redirect('stock')

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
    sale = Sales.objects.get(id=id)
    sale.delete()
    return redirect('save')


def edit_sale(request, id):
    sale = get_object_or_404(Sales, id=id)
    stocks = Stock.objects.all()   

    if request.method == 'POST':
        sale.name_id = request.POST.get('name')
        sale.quantity = request.POST.get('quantity')
        sale.unit_price = request.POST.get('unit_price')
        sale.date = request.POST.get('date')
        sale.customer_name = request.POST.get('customer_name')
        sale.customer_contact = request.POST.get('customer_contact')

        sale.save()
        return redirect('save',)

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
  
