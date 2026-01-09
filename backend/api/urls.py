"""
URL configuration for api project.

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

urlpatterns = [
    path('admin/', admin.site.urls),
    #Faltan los middleware y la programacion de las funciones
    #path('api/user/<int:pk>/', ,name="user_detail"),
    #path('api/customer/<int:pk>/', ,name="customer_details"),
    #path('api/supplier/<int:pk>/', ,name="supplier_details"),
    #path('api/product/<int:pk>/', ,name="product_detail"),
    #path('api/promotion/<int:pk>/', ,name="promotion_detail"),
]
