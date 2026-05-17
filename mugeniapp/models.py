from django.db import models
from django.utils.timezone import now

# Create your models here.

class Stock(models.Model):
    name = models.CharField(max_length=100) 
    category = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField(default=0)
    cost_price = models.PositiveIntegerField(default=0)
    selling_price = models.PositiveIntegerField(default=0)
    date = models.DateField()
    specifications = models.CharField(max_length=100, null=True)


    def __str__(self):
        return self.name

class Sales(models.Model):
    name = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.PositiveIntegerField()
    date = models.DateField()
    total_price = models.PositiveIntegerField(default=0)
    customer_name = models.CharField(max_length=100)
    customer_contact = models.CharField(max_length=100)

    distance = models.FloatField(default=0)
    transport_fee = models.PositiveIntegerField(default=0)

    grand_total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    

class Customer(models.Model):
    name = models.CharField(max_length=100)
    nin = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    product = models.CharField(max_length=100 ,null=True)
    amount = models.PositiveIntegerField(default=0)
    date = models.DateField(default=now)
    method_of_payment = models.CharField(max_length=100,default="Cash")
    def __str__(self):
        return self.name
    


    
class Supplier(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    supplier_name = models.CharField(max_length=100)
    supplier_contact = models.CharField(
    max_length=20,
    null=True,
    blank=True
)
    quantity = models.PositiveIntegerField(default=0)
    cost_price = models.PositiveIntegerField(default=0)
    total_cost = models.PositiveIntegerField(default=0 , blank=True, null=True)
    date = models.DateField()
    method_of_payment = models.CharField(max_length=100,default="Cash")
    amount_paid = models.PositiveIntegerField(default=0)
    balance = models.PositiveIntegerField(default=0, blank=True, null=True)    

    def __str__(self):
        return self.supplier_name
    