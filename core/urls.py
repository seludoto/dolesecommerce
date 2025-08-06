from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('deals/', views.deals_view, name='deals'),
    path('registry/', views.registry_view, name='registry'),
    path('customer-service/', views.customer_service_view, name='customer_service'),
]
