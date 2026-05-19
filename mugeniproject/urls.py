"""
URL configuration for mugeniproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mugeniapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('stock/', views.stock, name='stock'),
    path('delete-stock/<int:id>/', views.delete_stock, name='delete_stock'),
     path('edit_stock/<int:id>/', views.edit_stock, name='edit_stock'),
    path('add/', views.add, name='add'),
    path('sales/', views.sales, name='sales'),
    path('save/', views.save, name='save'),
    path('delete-sale/<int:id>/', views.delete_sale, name='delete_sale'),
    path('sales_receipt/<int:id>/', views.sales_receipt, name='sales_receipt'),
   path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),                                                                                
    path('edit_sale/<int:id>/', views.edit_sale, name='edit_sale'),
    path('customer/', views.customer, name='customer'),
    path('customer_list/', views.customer_list, name='customer_list'),
    path('delete-customer/<int:id>/', views.delete_customer, name='delete_customer'),
    path('edit_customer/<int:id>/', views.edit_customer, name='edit_customer'),
    path('customer_receipt/<int:id>/', views.customer_receipt, name='customer_receipt'),
    path('supplier/',views.supplier, name='supplier'),
    path('supplier_view/',views.supplier_view, name='supplier_view'),
    path('edit_supplier/<int:id>/', views.edit_supplier, name='edit_supplier'),
    path('delete_supplier/<int:id>/', views.delete_supplier, name='delete_supplier'),
    path('supplier_receipt/<int:id>/', views.supplier_receipt, name='supplier_receipt'),
    path('reports/', views.reports, name='reports'),
]
