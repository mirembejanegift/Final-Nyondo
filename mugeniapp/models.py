from django.db import models
from django.utils.timezone import now

# Create your models here.

class Stock(models.Model):
    name = models.CharField(max_length=100) 
    category = models.CharField(max_length=100)
    quantity = models.IntegerField()
    cost_price = models.IntegerField(default=0)
    selling_price = models.IntegerField(default=0)
    date = models.DateField()
    supplier = models.CharField(max_length=100)
    specifications = models.CharField(max_length=100, null=True)


    def __str__(self):
        return self.name

class Sales(models.Model):
    name = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100)
    unit_price = models.IntegerField()
    date = models.DateField()
    customer_name = models.CharField(max_length=100)
    customer_contact = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Customer(models.Model):
    name = models.CharField(max_length=100)
    nin = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    product = models.CharField(max_length=100 ,null=True)
    amount = models.IntegerField(default=0)
    date = models.DateField(default=now)
    method_of_payment = models.CharField(max_length=100,default="Cash")
    def __str__(self):
        return self.name