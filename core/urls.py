from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('set-currency/', views.set_currency, name='set_currency'),
    path('deals/', views.deals_view, name='deals'),
    path('registry/', views.registry_view, name='registry'),
    path('customer-service/', views.customer_service_view, name='customer_service'),
    path('help/', views.help_view, name='help'),
    path('debug-static/', views.debug_static_view, name='debug_static'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
]
