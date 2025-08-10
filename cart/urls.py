from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    # Main cart views
    path('', views.cart_detail, name='cart_detail'),
    path('count/', views.get_cart_count, name='cart_count'),
    path('clear/', views.clear_cart, name='clear_cart'),
    
    # Cart item management
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    
    # Save for later functionality
    path('save-later/<int:item_id>/', views.save_for_later, name='save_for_later'),
    path('move-to-cart/<int:product_id>/', views.move_to_cart, name='move_to_cart'),
    
    # Promo code functionality
    path('apply-promo/', views.apply_promo_code, name='apply_promo_code'),
    path('remove-promo/<int:promo_id>/', views.remove_promo_code, name='remove_promo_code'),
    
    # Cart recovery for abandoned carts
    path('recover/<str:token>/', views.cart_recovery, name='cart_recovery'),
    
    # Legacy URLs for backward compatibility
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart_legacy'),
    path('ajax/add/', views.add_to_cart, name='ajax_add_to_cart'),
    path('ajax/update/', views.update_cart_item, name='ajax_update_cart'),
    path('ajax/count/', views.get_cart_count, name='ajax_cart_count'),
]
