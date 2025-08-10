from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # General payment URLs
    path('pay/<int:order_id>/', views.pay_order, name='pay_order'),
    path('history/', views.payment_history, name='payment_history'),
    path('methods/', views.payment_methods, name='payment_methods'),
    
    # Pi Coin payment URLs
    path('pay/pi/<int:order_id>/', views.pay_order_pi, name='pay_order_pi'),
    path('pi/callback/', views.pi_payment_callback, name='pi_payment_callback'),
    path('pi/status/<int:payment_id>/', views.check_pi_payment_status, name='check_pi_payment_status'),
    
    # M-Pesa payment URLs
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    
    # Phone Payment URLs
    path('phone/dashboard/', views.phone_payment_dashboard, name='phone_payment_dashboard'),
    path('phone/send/', views.send_money_to_phone, name='send_money_to_phone'),
    path('phone/request/', views.request_payment_from_phone, name='request_payment_from_phone'),
    
    # M-Pesa B2C Callbacks
    path('mpesa/b2c-result/', views.mpesa_b2c_result_callback, name='mpesa_b2c_result_callback'),
    path('mpesa/b2c-timeout/', views.mpesa_b2c_timeout_callback, name='mpesa_b2c_timeout_callback'),
    
    # Admin payment management URLs
    path('admin/list/', views.admin_payment_list, name='admin_payment_list'),
    path('admin/confirm-pi/<int:payment_id>/', views.confirm_pi_payment, name='confirm_pi_payment'),
    path('admin/pi-rates/', views.pi_rate_management, name='pi_rate_management'),
]
