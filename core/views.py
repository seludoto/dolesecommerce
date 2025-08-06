from django.shortcuts import render

from products.models import Product

def home(request):
    products = Product.objects.filter(is_active=True)[:3]
    return render(request, 'core/home.html', {'products': products})

def deals_view(request):
    return render(request, 'core/deals.html')

def registry_view(request):
    return render(request, 'core/registry.html')

def customer_service_view(request):
    return render(request, 'core/customer_service.html')
