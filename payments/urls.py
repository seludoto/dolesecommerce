from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('pay/<int:order_id>/', views.pay_order, name='pay_order'),
    path('pay/pi/<int:order_id>/', views.pay_order_pi, name='pay_order_pi'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa_callback'),
    path('history/', views.payment_history, name='payment_history'),
    # Admin payment management
    path('admin/list/', views.admin_payment_list, name='admin_payment_list'),
    path('admin/confirm-pi/<int:payment_id>/', views.confirm_pi_payment, name='confirm_pi_payment'),
]
