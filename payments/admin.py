from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'payment_method', 'status', 'created_at')
    search_fields = ('order__id', 'payment_method', 'status', 'payment_id', 'pi_wallet_address')
    list_filter = ('payment_method', 'status', 'created_at')
