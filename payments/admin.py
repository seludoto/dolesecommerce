from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Payment, 
    MpesaB2CTransaction, MpesaC2BTransaction, PhonePayment
)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order_link', 'amount', 'payment_method', 'status', 
        'created_at'
    ]
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = [
        'order__id', 'payment_id', 'order__user__username'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'gateway_response_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'amount', 'payment_method', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_id', 'failure_reason', 'processed_by')
        }),
        ('System Information', {
            'fields': ('gateway_response_display', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, f'Order #{obj.order.id}')
    order_link.short_description = 'Order'
    
    def gateway_response_display(self, obj):
        if obj.gateway_response:
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">{}</pre>',
                obj.gateway_response[:500] + ('...' if len(obj.gateway_response) > 500 else '')
            )
        return "No response data"
    gateway_response_display.short_description = 'Gateway Response'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'processed_by')


# Custom admin site configuration
admin.site.site_header = "E-Commerce Payment Administration"
admin.site.site_title = "Payment Admin"
admin.site.index_title = "Payment Management Dashboard"


@admin.register(MpesaB2CTransaction)
class MpesaB2CTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'conversation_id', 'formatted_phone_display', 'amount', 'status', 
        'response_code', 'created_at', 'transaction_receipt'
    ]
    list_filter = ['status', 'response_code', 'created_at']
    search_fields = [
        'conversation_id', 'phone_number', 'transaction_id', 
        'transaction_receipt', 'receiver_party_public_name'
    ]
    readonly_fields = [
        'conversation_id', 'originator_conversation_id', 'response_code',
        'response_description', 'transaction_id', 'transaction_receipt',
        'receiver_party_public_name', 'transaction_completed_date_time',
        'b2c_charges_paid_account_available_funds', 'b2c_utility_account_available_funds',
        'b2c_working_account_available_funds', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'payment', 'conversation_id', 'originator_conversation_id',
                'phone_number', 'amount', 'remarks', 'occasion', 'status'
            )
        }),
        ('Response Information', {
            'fields': (
                'response_code', 'response_description', 'transaction_id',
                'transaction_receipt', 'receiver_party_public_name'
            ),
            'classes': ('collapse',)
        }),
        ('Account Information', {
            'fields': (
                'b2c_charges_paid_account_available_funds',
                'b2c_utility_account_available_funds', 
                'b2c_working_account_available_funds'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('transaction_completed_date_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def formatted_phone_display(self, obj):
        return obj.formatted_phone
    formatted_phone_display.short_description = 'Phone Number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment')


@admin.register(MpesaC2BTransaction)
class MpesaC2BTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'checkout_request_id', 'formatted_phone_display', 'amount', 'status',
        'result_code', 'created_at', 'mpesa_receipt_number'
    ]
    list_filter = ['status', 'result_code', 'created_at']
    search_fields = [
        'checkout_request_id', 'merchant_request_id', 'phone_number',
        'account_reference', 'mpesa_receipt_number'
    ]
    readonly_fields = [
        'checkout_request_id', 'merchant_request_id', 'result_code',
        'result_desc', 'mpesa_receipt_number', 'transaction_date',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Details', {
            'fields': (
                'payment', 'checkout_request_id', 'merchant_request_id',
                'phone_number', 'amount', 'account_reference', 'transaction_desc', 'status'
            )
        }),
        ('Response Information', {
            'fields': (
                'result_code', 'result_desc', 'mpesa_receipt_number', 'transaction_date'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def formatted_phone_display(self, obj):
        return obj.formatted_phone
    formatted_phone_display.short_description = 'Phone Number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment')


@admin.register(PhonePayment)
class PhonePaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'payment_type', 'provider', 'formatted_phone_display', 
        'amount', 'status', 'initiated_by', 'created_at'
    ]
    list_filter = ['payment_type', 'provider', 'status', 'created_at']
    search_fields = [
        'reference', 'phone_number', 'description', 'transaction_id',
        'receipt_number', 'initiated_by__username'
    ]
    readonly_fields = [
        'reference', 'transaction_id', 'receipt_number', 'created_at', 'completed_at'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Payment Details', {
            'fields': (
                'payment_type', 'provider', 'phone_number', 'amount',
                'description', 'reference', 'status'
            )
        }),
        ('Transaction Information', {
            'fields': (
                'transaction_id', 'receipt_number', 'initiated_by'
            ),
            'classes': ('collapse',)
        }),
        ('Related Transactions', {
            'fields': ('mpesa_b2c', 'mpesa_c2b'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def formatted_phone_display(self, obj):
        return obj.formatted_phone
    formatted_phone_display.short_description = 'Phone Number'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'initiated_by', 'mpesa_b2c', 'mpesa_c2b'
        )
