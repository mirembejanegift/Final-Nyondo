from email import errors
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime, date, timedelta
from django.db import transaction
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models import Sum, Count, F
from django.utils import timezone
from .models import Stock, Sales, Customer, Supplier



# # Create your views here.
# THIS IS THE HOME PAGE VIEW
def index(request):
    return render(request, 'index.html')



# THIS IS THE LOGIN VIEW. I USED DJANGO'S BUILT-IN AUTHENTICATION SYSTEM TO HANDLE USER LOGIN.
# i used a supperuser check for admin role and group checks for sales and stock manager roles. 
def login_view(request):

# I use the data dictionary to temporarily store user input and the errors dictionary to keep track of validation errors before saving data to the database.
    errors = {}
    data = {}

    if request.method == "POST":

        # GET FORM DATA
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        data["username"] = username

        # FIELD VALIDATIONS
        if not username:
            errors["username"] = "Username is required."

        if not password:
            errors["password"] = "Password is required."

        # STOP EARLY IF FIELD ERRORS EXIST
        if errors:
            return render(request, "login.html", {
                "errors": errors,
                "data": data
            })

        # AUTHENTICATE USER
        user = authenticate(request, username=username, password=password)

        if user is not None:

            if not user.is_active:
                messages.error(request, "Your account has been disabled.")
                return render(request, "login.html")

            login(request, user)

            messages.success(request, f"Welcome back, {user.username}!")

            # ROLE-BASED REDIRECTS
            if user.is_superuser or user.groups.filter(name="admin").exists():
                return redirect("dashboard")

            elif user.groups.filter(name="sales").exists():
                return redirect("save")

            elif user.groups.filter(name="stock_manager").exists():
                return redirect("add")

            else:
                messages.error(request, "You do not have permission to access the system.")
                return redirect("login")

        else:
            errors["general"] = "Invalid username or password."
            return render(request, "login.html", {
                "errors": errors,
                "data": data
            })

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
    # Get today's date
    today = date.today()

    # Calculate the date 7 days ago
    one_week_ago = today - timedelta(days=7)

    # Dictionary to store validation errors
    errors = {}

    # Dictionary to store form data entered by the user
    data = {}

    # Check if the form was submitted
    if request.method == 'POST':

        # Get values from the form
        data['name'] = request.POST.get('name')
        data['category'] = request.POST.get('category')
        data['quantity'] = request.POST.get('quantity')
        data['supplier'] = request.POST.get('supplier')
        data['cost_price'] = request.POST.get('cost_price')
        data['selling_price'] = request.POST.get('selling_price')
        data['date'] = request.POST.get('date')

        # Validate product name
        if not data['name']:
            errors['name'] = "Product name is required."
        else:
            # Remove extra spaces and capitalize words
            data['name'] = data['name'].strip().title()

        # Validate category
        if not data['category']:
            errors['category'] = "Category is required."

        # Validate quantity
        if not data['quantity']:
            errors['quantity'] = "Quantity is required."
        else:
            try:
                data['quantity'] = int(data['quantity'])

                # Quantity must be greater than zero
                if data['quantity'] <= 0:
                    errors['quantity'] = "Quantity must be greater than 0."

            except:
                errors['quantity'] = "Quantity must be a valid number."

        # Validate supplier
        if not data['supplier']:
            errors['supplier'] = "Supplier is required."

        # Validate cost price
        if not data['cost_price']:
            errors['cost_price'] = "Cost price is required."
        else:
            try:
                data['cost_price'] = float(data['cost_price'])

                # Cost price cannot be zero or negative
                if data['cost_price'] <= 0:
                    errors['cost_price'] = "Cost price must be greater than 0."

            except:
                errors['cost_price'] = "Cost price must be a number."

        # Validate selling price
        if not data['selling_price']:
            errors['selling_price'] = "Selling price is required."
        else:
            try:
                data['selling_price'] = float(data['selling_price'])

                # Selling price cannot be zero or negative
                if data['selling_price'] <= 0:
                    errors['selling_price'] = "Selling price must be greater than 0."

            except:
                errors['selling_price'] = "Selling price must be a number."

        # Validate stock date
        if not data['date']:
            errors['date'] = "Date is required."
        else:
            try:
                # Convert the entered date into a Python date object
                stock_date = datetime.strptime(
                    data['date'], "%Y-%m-%d"
                ).date()

                # Do not allow future dates
                if stock_date > today:
                    errors['date'] = "Date cannot be in the future."

                # Do not allow dates older than one week
                if stock_date < one_week_ago:
                    errors['date'] = "Date cannot be older than 1 week."

            except:
                errors['date'] = "Invalid date format."

        # If there are validation errors,
        # return the form with the entered data and error messages
        if errors:
            return render(request, 'stock.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })

        # Check whether the product already exists
        # If it doesn't exist, create a new stock record
        stock_obj, created = Stock.objects.get_or_create(
            name=data['name'],
            defaults={
                'category': data['category'],
                'supplier': data['supplier'],
                'quantity': 0,
                'cost_price': data['cost_price'],
                'selling_price': data['selling_price'],
                'date': stock_date,
            }
        )

        # Update stock details
        stock_obj.category = data['category']
        stock_obj.supplier = data['supplier']
        stock_obj.cost_price = data['cost_price']
        stock_obj.selling_price = data['selling_price']
        stock_obj.date = stock_date

        # Add the new quantity to the existing stock quantity
        stock_obj.quantity += data['quantity']

        # Save changes to the database
        stock_obj.save()

        # Redirect after successful stock addition
        return redirect('/add/')

    # Display an empty form when the page is first loaded
    return render(request, 'stock.html', {
        'today': today,
        'one_week_ago': one_week_ago,
        'errors': {},
        'data': {}
    })





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
@transaction.atomic  # Ensures all database actions succeed or fail together (prevents partial updates)
def sales(request):

    # Get today's date (used to restrict sales to today only)
    today = date.today()

    # Get all stock items to display in dropdown
    stocks = Stock.objects.all()

    # Dictionaries to store validation errors and form data
    errors = {}
    data = {}

    # Check if form is submitted
    if request.method == 'POST':

        # Get data from the form
        data['stock_id'] = request.POST.get('stock_id')
        data['quantity'] = request.POST.get('quantity')
        data['date'] = request.POST.get('date')
        data['customer_name'] = request.POST.get('customer_name')
        data['customer_contact'] = request.POST.get('customer_contact')
        data['distance'] = request.POST.get('distance')

        #  VALIDATION SECTION 

        # Validate stock selection
        if not data['stock_id']:
            errors['stock_id'] = "Please select an item."

        # Validate quantity
        if not data['quantity']:
            errors['quantity'] = "Quantity is required."
        else:
            try:
                data['quantity'] = int(data['quantity'])

                # Quantity must be greater than 0
                if data['quantity'] <= 0:
                    errors['quantity'] = "Quantity must be greater than 0."
            except:
                errors['quantity'] = "Quantity must be a number."

        # Validate delivery distance
        if not data['distance']:
            errors['distance'] = "Distance is required."
        else:
            try:
                data['distance'] = float(data['distance'])

                # Distance cannot be negative
                if data['distance'] < 0:
                    errors['distance'] = "Distance cannot be negative."
            except:
                errors['distance'] = "Distance must be a number."

        # Validate date (sales only allowed today)
        if not data['date']:
            errors['date'] = "Date is required."
        else:
            try:
                stock_date = datetime.strptime(
                    data['date'], "%Y-%m-%d"
                ).date()

                # Only allow today's sales
                if stock_date != today:
                    errors['date'] = "Sales can only be recorded for today."

            except:
                errors['date'] = "Invalid date format."

        # Validate customer name
        if not data['customer_name']:
            errors['customer_name'] = "Customer name is required."

        # Validate customer contact
        if not data['customer_contact']:
            errors['customer_contact'] = "Customer contact is required."
        elif not data['customer_contact'].isdigit():
            errors['customer_contact'] = "Contact must be numbers only."
        elif len(data['customer_contact']) != 10:
            errors['customer_contact'] = "Contact must be 10 digits."

        # If there are errors, return form with error messages
        if errors:
            return render(request, 'sales.html', {
                'stocks': stocks,
                'errors': errors,
                'data': data
            })

        #  BUSINESS LOGIC SECTION 

        # Get selected stock item from database
        stock = get_object_or_404(Stock, id=data['stock_id'])

        # Get selling price per unit
        unit_price = stock.selling_price

        # Check if requested quantity is available in stock
        if data['quantity'] > stock.quantity:
            errors['quantity'] = f"Only {stock.quantity} items available."

            return render(request, 'sales.html', {
                'stocks': stocks,
                'errors': errors,
                'data': data
            })

        # Calculate total price (quantity × unit price)
        total_price = data['quantity'] * unit_price

        # Calculate transport fee
        # Free delivery for small orders close by
        if data['distance'] <= 10 and total_price <= 500000:
            transport_fee = 0
        else:
            transport_fee = 30000

        # Final total including transport
        grand_total = total_price + transport_fee

        # Save the sale record to database
        Sales.objects.create(
            name=stock,
            quantity=data['quantity'],
            unit_price=unit_price,
            total_price=total_price,
            distance=data['distance'],
            transport_fee=transport_fee,
            grand_total=grand_total,
            date=stock_date,
            customer_name=data['customer_name'],
            customer_contact=data['customer_contact']
        )

        # Reduce stock quantity after sale
        stock.quantity -= data['quantity']
        stock.save()

        # Success message for user
        messages.success(request, "Sale recorded successfully.")

        # Redirect to saved sales page
        return redirect('save')

    # GET REQUEST (PAGE LOAD)  

    # Show empty form when page is first opened
    return render(request, 'sales.html', {
        'stocks': stocks,
        'today': today,
        'errors': {},
        'data': {}
    })



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
        sale = get_object_or_404(Sales, id=id)  
        sale.delete()
    return redirect('save')



@login_required
def edit_sale(request, id):
    if not request.user.is_superuser:
        return redirect('save')

    sale = get_object_or_404(Sales, id=id)
    stocks = Stock.objects.all()

    if request.method == 'POST':

        stock_id = request.POST.get('name')
        quantity = request.POST.get('quantity')
        distance = request.POST.get('distance')
        date = request.POST.get('date')
        customer_name = request.POST.get('customer_name')
        customer_contact = request.POST.get('customer_contact')

        errors = []

        try:
            stock = Stock.objects.get(id=int(stock_id))
        except (Stock.DoesNotExist, ValueError, TypeError):
            errors.append("Invalid product selected")


        try:
            quantity = int(quantity)
            if quantity <= 0:
                errors.append("Quantity must be greater than 0")
        except:
            errors.append("Quantity must be a valid number")

  
        try:
            distance = float(distance)
            if distance < 0:
                errors.append("Distance cannot be negative")
        except:
            errors.append("Distance must be a valid number")

        if not date:
            errors.append("Date is required")

        if errors:
            for e in errors:
                messages.error(request, e)

            return render(request, 'edit_sale.html', {
                'sale': sale,
                'stocks': stocks
            })

        sale.name = stock
        sale.quantity = quantity
        sale.distance = distance
        sale.date = date
        sale.customer_name = customer_name
        sale.customer_contact = customer_contact

        sale.unit_price = stock.selling_price  

        sale.total_price = stock.selling_price * quantity

        sale.save()

        messages.success(request, "Sale updated successfully")
        return redirect('save')

    return render(request, 'edit_sale.html', {
        'sale': sale,
        'stocks': stocks
    })



# CUSTOMER LIST VIEW
@login_required
def customer(request):
    customers = Customer.objects.all().order_by('-id')
    return render(request, "customer.html", {
        "customers": customers
    })



# THIS IS THE CUSTOMER LIST VIEW. IT DISPLAYS A LIST OF ALL CUSTOMERS IN THE DATABASE AND PROVIDES OPTIONS TO EDIT OR DELETE CUSTOMER RECORDS.
@login_required
def customer_list(request):

    # Get today's date
    today = datetime.today().date()

    # Calculate the date exactly 7 days before today
    # This will be used to prevent users from entering very old dates
    one_week_ago = today - timedelta(days=7)

    # Dictionary to store validation error messages
    errors = {}

    # Dictionary to store form data entered by the user
    # This helps us refill the form if validation fails
    data = {}

    # Run this block only when the form is submitted
    if request.method == 'POST':

        # Retrieve data from the submitted form and remove extra spaces
        data['name'] = request.POST.get('name', '').strip()
        data['nin'] = request.POST.get('nin', '').strip()
        data['email'] = request.POST.get('email', '').strip()
        data['contact'] = request.POST.get('contact', '').strip()
        data['product'] = request.POST.get('product', '').strip()
        data['amount'] = request.POST.get('amount', '').strip()
        data['date'] = request.POST.get('date', '').strip()

        # CUSTOMER NAME VALIDATIO

        # Ensure the customer name is provided
        if not data['name']:
            errors['name'] = "Customer name is required."
        # NIN VALIDATION

        # Check if NIN was entered
        if not data['nin']:
            errors['nin'] = "National ID is required."

        # Check that NIN contains exactly 14 characters
        elif len(data['nin']) != 14:
            errors['nin'] = "NIN must be exactly 14 characters (letters and digits allowed)."

        # Check that NIN contains only letters and numbers
        elif not data['nin'].isalnum():
            errors['nin'] = "NIN must contain only letters and numbers (no symbols or spaces)."

        # EMAIL VALIDATION

        # Ensure email is provided
        if not data['email']:
            errors['email'] = "Email is required."

        # Basic email validation
        elif "@" not in data['email']:
            errors['email'] = "Enter a valid email address."

        # CONTACT VALIDATION

        # Ensure contact number is entered
        if not data['contact']:
            errors['contact'] = "Contact number is required."

        # Ensure contact contains only digits and is exactly 10 digits long
        elif not data['contact'].isdigit() or len(data['contact']) != 10:
            errors['contact'] = "Contact must be a valid 10-digit number."

        # PRODUCT VALIDATION

        # Ensure product name is entered
        if not data['product']:
            errors['product'] = "Product name is required."

        # AMOUNT VALIDATION

        # Ensure amount is entered
        if not data['amount']:
            errors['amount'] = "Amount is required."

        else:
            try:
                # Convert amount from text to integer
                data['amount'] = int(data['amount'])

                # Amount must be greater than zero
                if data['amount'] <= 0:
                    errors['amount'] = "Amount must be greater than 0."

            except ValueError:
                # User entered letters or invalid characters
                errors['amount'] = "Amount must be a number."
        # DATE VALIDATION

        # Ensure date is entered
        if not data['date']:
            errors['date'] = "Date is required."

        else:
            try:
                # Convert date string into a Python date object
                customer_date = datetime.strptime(
                    data['date'],
                    "%Y-%m-%d"
                ).date()

                # Prevent future dates
                if customer_date > today:
                    errors['date'] = "Future dates are not allowed."

                # Prevent dates older than 7 days
                if customer_date < one_week_ago:
                    errors['date'] = "Date cannot be older than 7 days."

            except ValueError:
                # Invalid date format entered
                errors['date'] = "Invalid date format."

        # CHECK FOR VALIDATION ERRORS

        # If any validation errors exist,
        # return the form with the entered data and error messages
        if errors:
            return render(request, 'customer_list.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })
        # SAVE CUSTOMER
        # Create a new customer object using validated data
        new_customer = Customer(
            name=data['name'],
            nin=data['nin'],
            email=data['email'],
            contact=data['contact'],
            product=data['product'],
            amount=data['amount'],
            date=customer_date
        )

        # Save the customer record to the database
        new_customer.save()

        # Display a success message after saving
        messages.success(request, "Customer added successfully.")

        # Redirect to prevent duplicate form submissions
        return redirect('customer')

    # INITIAL PAGE LOAD
    

    # When the page is opened for the first time,
    # display an empty form
    return render(request, 'customer_list.html', {
        'today': today,
        'one_week_ago': one_week_ago,
        'errors': {},
        'data': {}
    })



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
    customer = get_object_or_404(Customer, id=id)
    customer.delete()

    messages.success(request, "Customer deleted successfully")

    return redirect('customer')



@login_required
def edit_customer(request, id):

    customer = get_object_or_404(Customer, id=id)
    customers = Customer.objects.all()

    if request.method == 'POST':

        # GET FORM DATA
        name = request.POST.get('name')
        nin = request.POST.get('nin')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        product = request.POST.get('product')
        amount = request.POST.get('amount')
        customer_date = request.POST.get('date')

        if not all([name, nin, email, contact, product, amount, customer_date]):
            messages.error(request, "All fields are required")
            return redirect('edit_customer', id=id)

        if len(nin) != 14:
            messages.error(request, "NIN must be exactly 14 characters")
            return redirect('edit_customer', id=id)

        if not contact.isdigit() or len(contact) != 10:
            messages.error(request, "Contact must be exactly 10 digits")
            return redirect('edit_customer', id=id)

        if "@" not in email or "." not in email:
            messages.error(request, "Enter a valid email address")
            return redirect('edit_customer', id=id)

        try:
            amount = float(amount)

            if amount <= 0:
                messages.error(request, "Amount must be greater than zero")
                return redirect('edit_customer', id=id)

        except ValueError:
            messages.error(request, "Amount must be numeric")
            return redirect('edit_customer', id=id)

        try:
            entered_date = datetime.strptime(customer_date, "%Y-%m-%d").date()

        except ValueError:
            messages.error(request, "Invalid date format")
            return redirect('edit_customer', id=id)

        if entered_date > date.today():
            messages.error(request, "Date cannot be in the future")
            return redirect('edit_customer', id=id)

        customer.name = name
        customer.nin = nin
        customer.email = email
        customer.contact = contact
        customer.product = product
        customer.amount = amount
        customer.date = entered_date

        customer.save()

        messages.success(request, "Customer updated successfully")

        return redirect('customer')

    return render(request, 'edit_customer_list.html', {
        'customer': customer,
        'customers': customers
    })




# THIS IS THE SUPPLIER VIEW. IT HANDLES THE LOGIC FOR ADDING SUPPLIERS, INCLUDING VALIDATING INPUT AND SAVING SUPPLIER RECORDS TO THE DATABASE.
@login_required
def supplier(request):

    # Allow only superusers to access the supplier page
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('index')

    # Get today's date and calculate the date 7 days ago
    # Used to validate supply dates
    today = datetime.today().date()
    one_week_ago = today - timedelta(days=7)

    # Store validation errors and form data
    errors = {}
    data = {}

    # Run when the supplier form is submitted
    if request.method == 'POST':

        # Retrieve submitted form data
        data = request.POST

        product_name = data.get('product_name')
        supplier_name = data.get('supplier_name')
        supplier_contact = data.get('supplier_contact')

        quantity = data.get('quantity')
        cost_price = data.get('cost_price')

        amount_paid = data.get('amount_paid') or 0
        supplier_date_str = data.get('date')
        method_of_payment = data.get('method_of_payment')

        # REQUIRED FIELD VALIDATION
   

        if not product_name:
            errors['product_name'] = "Item is required"

        if not supplier_name:
            errors['supplier_name'] = "Supplier name is required"

        if not supplier_contact:
         errors['supplier_contact'] = "Supplier contact is required"
        elif not supplier_contact.isdigit():
         errors['supplier_contact'] = "Contact must contain only digits"
        elif len(supplier_contact) != 10:
         errors['supplier_contact'] = "Contact must be exactly 10 digits"

        if not quantity:
            errors['quantity'] = "Quantity is required"

        if not cost_price:
            errors['cost_price'] = "Cost price is required"

        if not supplier_date_str:
            errors['date'] = "Supply date is required"

        if not method_of_payment:
            errors['method_of_payment'] = "Select payment method"

        # Return form with error messages if validation fails
        if errors:
            return render(request, 'supplier.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })

  

        try:
            quantity = int(quantity)
            cost_price = float(cost_price)
            amount_paid = float(amount_paid)

        except ValueError:
            # User entered invalid numeric values
            errors['general'] = "Invalid number input"

            return render(request, 'supplier.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })

        # NUMERIC VALUE VALIDATION
    

        # Quantity must be greater than zero
        if quantity <= 0:
            errors['quantity'] = "Quantity must be greater than zero"

        # Cost price must be greater than zero
        if cost_price <= 0:
            errors['cost_price'] = "Cost price must be greater than zero"

        # DATE VALIDATION
   

        try:
            # Convert supplied date string to a date object
            supplier_date = datetime.strptime(
                supplier_date_str,
                "%Y-%m-%d"
            ).date()

        except ValueError:
            errors['date'] = "Invalid date"

        # Return if conversion or validation failed
        if errors:
            return render(request, 'supplier.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })

        # Prevent future supply dates
        if supplier_date > today:
            errors['date'] = "Future dates are not allowed"

        # Prevent dates older than 7 days
        if supplier_date < one_week_ago:
            errors['date'] = "Date cannot be older than 7 days"

        # COST CALCULATIONS
       

        # Calculate total cost of supplied stock
        total_cost = quantity * cost_price

        # For cash payments, supplier is fully paid
        if method_of_payment == 'cash':
            amount_paid = total_cost
            balance = 0

        # For credit payments, calculate remaining balance
        else:
            balance = total_cost - amount_paid

        # Prevent payment amounts greater than total cost
        if amount_paid > total_cost:
            errors['amount_paid'] = "Overpayment is not allowed"

        # Return form if any errors exist
        if errors:
            return render(request, 'supplier.html', {
                'errors': errors,
                'data': data,
                'today': today,
                'one_week_ago': one_week_ago
            })
        # SAVE SUPPLIER RECORD  

        Supplier.objects.create(
            product_name = product_name,
            supplier_name = supplier_name,
            supplier_contact = supplier_contact,
            quantity = quantity,
            cost_price = cost_price,
            total_cost = total_cost,
            amount_paid = amount_paid,
            balance = balance,
            date = supplier_date,
            method_of_payment = method_of_payment
        )

        # UPDATE STOCK INVENTORY

        # Create stock item if it does not exist
        # Otherwise retrieve the existing stock item
        stock, created = Stock.objects.get_or_create(
            name=product_name,
            defaults={
                "quantity": 0,
                "cost_price": cost_price,
                "selling_price": 0,
                "date": supplier_date
            }
        )

        # Increase stock quantity with newly supplied items
        stock.quantity += quantity

        # Update latest cost price and supply date
        stock.cost_price = cost_price
        stock.date = supplier_date

        # Save stock changes
        stock.save()

        # Display success message
        messages.success(
            request,
            "Supplier added and stock updated successfully."
        )

        # Redirect to prevent duplicate form submissions
        return redirect('supplier_view')


    # Display empty form when page is opened
    return render(request, 'supplier.html', {
        'today': today,
        'one_week_ago': one_week_ago,
        'errors': {},
        'data': {}
    })





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

        product_name = request.POST.get('product_name')
        supplier_name = request.POST.get('supplier_name')
        quantity = request.POST.get('quantity')
        cost_price = request.POST.get('cost_price')
        supplier_date = request.POST.get('date')
        method_of_payment = request.POST.get('method_of_payment')
        amount_paid = request.POST.get('amount_paid')

        if not product_name:
            messages.error(request, "Product name is required")
            return redirect('edit_supplier', id=id)

        if not supplier_name:
            messages.error(request, "Supplier name is required")
            return redirect('edit_supplier', id=id)

        if not quantity:
            messages.error(request, "Quantity is required")
            return redirect('edit_supplier', id=id)

        if not cost_price:
            messages.error(request, "Cost price is required")
            return redirect('edit_supplier', id=id)

        if not supplier_date:
            messages.error(request, "Date is required")
            return redirect('edit_supplier', id=id)

        if not amount_paid:
            messages.error(request, "Amount paid is required")
            return redirect('edit_supplier', id=id)

        try:
            quantity = int(quantity)
            cost_price = float(cost_price)
            amount_paid = float(amount_paid)

        except ValueError:

            messages.error(
                request,
                "Quantity, cost price and amount paid must be valid numbers"
            )

            return redirect('edit_supplier', id=id)

        if quantity <= 0:

            messages.error(request, "Quantity must be greater than 0")

            return redirect('edit_supplier', id=id)

        if cost_price <= 0:

            messages.error(request, "Cost price must be greater than 0")

            return redirect('edit_supplier', id=id)

        if amount_paid < 0:

            messages.error(request, "Amount paid cannot be negative")

            return redirect('edit_supplier', id=id)

        try:
            entered_date = datetime.strptime(
                supplier_date,
                '%Y-%m-%d'
            ).date()

        except ValueError:

            messages.error(request, "Invalid date format")

            return redirect('edit_supplier', id=id)

        if entered_date > date.today():

            messages.error(request, "Date cannot be in the future")

            return redirect('edit_supplier', id=id)

        total_cost = quantity * cost_price

        if amount_paid > total_cost:

            messages.error(
                request,
                "Amount paid cannot exceed total cost"
            )

            return redirect('edit_supplier', id=id)

        balance = total_cost - amount_paid

        supplier.product_name = product_name.strip().title()
        supplier.supplier_name = supplier_name.strip().title()
        supplier.quantity = quantity
        supplier.cost_price = cost_price
        supplier.date = entered_date
        supplier.method_of_payment = method_of_payment
        supplier.amount_paid = amount_paid

        supplier.total_cost = total_cost
        supplier.balance = balance

        supplier.save()

        messages.success(request, "Supplier updated successfully")

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




# THIS IS THE GENERAL REPORT FOR THE SYSTEM
@login_required
def reports(request):
    # Get today's date
    today = timezone.now().date()

    # Get all sales records ordered from latest to oldest
    sales = Sales.objects.all().order_by('-id')

    
    # TODAY'S SALES
    
    # Sum all total_price for sales made today
    today_sales = (
        Sales.objects.filter(date=today)
        .aggregate(total=Sum('total_price'))['total'] or 0
    )

    # Re-define today using datetime (you can standardize this later)
    today = datetime.today().date()

    # WEEKLY SALES (LAST WEEK)
    
    # Find current week's Monday and Sunday
    current_week_monday = today - timedelta(days=today.weekday())
    current_week_sunday = current_week_monday + timedelta(days=6)

    # Calculate previous week's Monday and Sunday
    last_week_monday = current_week_monday - timedelta(days=7)
    last_week_sunday = current_week_monday - timedelta(days=1)

    # Sum sales for last week only
    week_sales = (
        Sales.objects.filter(date__range=[last_week_monday, last_week_sunday])
        .aggregate(total=Sum('total_price'))['total'] or 0
    )

    
    # MONTHLY SALES
    
    # Sum all sales in the current month and year
    month_sales = (
        Sales.objects.filter(
            date__month=today.month,
            date__year=today.year
        ).aggregate(total=Sum('total_price'))['total'] or 0
    )


    # TOTAL PROFIT
    
    # Profit = (selling price - cost price) * quantity
    # Uses F() expressions for database-level calculation
    total_profit = (
        Sales.objects.aggregate(
            profit=Sum(
                (F('unit_price') - F('name__cost_price')) * F('quantity')
            )
        )['profit'] or 0
    )

    
    # MOST SOLD PRODUCT

    # Group sales by product name and sum quantities
    most_sold = (
        Sales.objects.values('name__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')
        .first()
    )

    # Extract product name safely
    most_sold_item = most_sold['name__name'] if most_sold else "No sales yet"

    
    # TOTAL UNIQUE CUSTOMERS
    
    # Count distinct customer names
    total_customers = (
        Sales.objects.values('customer_name')
        .distinct()
        .count()
    )

    # LOW STOCK ITEMS
    
    # Products where stock quantity is less than 10
    low_stock_items = Stock.objects.filter(quantity__lt=10)

    
    # TOP PRODUCTS
    
    # Get top 2 most sold products
    top_products = (
        Sales.objects.values('name__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:2]
    )

    
    # CONTEXT (DATA SENT TO TEMPLATE)
    context = {
        'today': today,
        'sales': sales,

        'today_sales': today_sales,
        'week_sales': week_sales,
        'month_sales': month_sales,
        'total_profit': total_profit,
        'most_sold_item': most_sold_item,
        'total_customers': total_customers,

        'low_stock_items': low_stock_items,
        'top_products': top_products,
    }

    # Render the reports page with all calculated data
    return render(request, 'reports.html', context)