from django.urls import path
from . import views

app_name = 'promotions'

urlpatterns = [
    # Flash Sales
    path('flash-sales/', views.flash_sales_list, name='flash_sales_list'),
    path('flash-sales/<int:flash_sale_id>/', views.flash_sale_detail, name='flash_sale_detail'),
    path('flash-sales/add-to-cart/<int:flash_sale_product_id>/', views.add_flash_sale_to_cart, name='add_flash_sale_to_cart'),
    path('flash-sales/time-remaining/<int:flash_sale_id>/', views.get_flash_sale_time_remaining, name='flash_sale_time_remaining'),
]
