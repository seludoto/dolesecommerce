from django.urls import path
from . import views

app_name = 'stores'

urlpatterns = [
    # Store Application URLs
    path('apply/', views.apply_for_store, name='apply_for_store'),
    path('application-status/', views.application_status, name='application_status'),
    
    # Seller Dashboard URLs
    path('dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('settings/', views.store_settings, name='store_settings'),
    path('analytics/', views.store_analytics, name='store_analytics'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Product Management URLs
    path('products/', views.manage_products, name='manage_products'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/toggle-status/', views.toggle_product_status, name='toggle_product_status'),
    
    # Public Store URLs
    path('', views.store_list, name='store_list'),
    path('<slug:slug>/', views.store_detail, name='store_detail'),
    path('<int:store_id>/follow/', views.follow_store, name='follow_store'),
]
