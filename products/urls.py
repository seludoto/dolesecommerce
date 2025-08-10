from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Main product views
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    
    # Basic search and filtering (simplified)
    path('search/', views.product_list, name='advanced_search'),
    path('category/<slug:category_slug>/', views.category_view, name='category_products'),
    
    # API endpoints for AJAX
    path('api/search/', views.api_search, name='api_search'),
]
