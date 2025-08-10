from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart management
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('cart/checkout/', views.cart_checkout, name='cart_checkout'),
    
    # Order management
    path('', views.order_list, name='order_list'),
    path('history/', views.order_list, name='order_history'),  # Alias for order_list
    path('<int:pk>/', views.order_detail, name='order_detail'),
    
    # Direct purchase
    path('buy/<int:product_id>/', views.buy_now, name='buy_now'),
]
