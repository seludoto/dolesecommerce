from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Payment, PiCoinRate, PiPaymentTransaction, 
    MpesaB2CTransaction, MpesaC2BTransaction, PhonePayment
)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'order_link', 'amount', 'payment_method', 'status', 
        'pi_amount_display', 'created_at', 'payment_actions'
    ]
    list_filter = ['payment_method', 'status', 'pi_status', 'created_at']
    search_fields = [
        'order__id', 'payment_id', 'pi_payment_id', 
        'pi_wallet_address', 'order__user__username'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'gateway_response_display', 
        'pi_amount_display'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('order', 'amount', 'payment_method', 'status')
        }),
        ('Payment Details', {
            'fields': ('payment_id', 'failure_reason', 'processed_by')
        }),
        ('Pi Coin Details', {
            'fields': (
                'pi_payment_id', 'pi_wallet_address', 'pi_amount', 
                'pi_txid', 'pi_status', 'pi_exchange_rate'
            ),
            'classes': ('collapse',)
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
    
    def pi_amount_display(self, obj):
        if obj.pi_amount:
            return f"{obj.pi_amount:.7f} π"
        return "-"
    pi_amount_display.short_description = 'Pi Amount'
    
    def gateway_response_display(self, obj):
        if obj.gateway_response:
            return format_html(
                '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">{}</pre>',
                obj.gateway_response[:500] + ('...' if len(obj.gateway_response) > 500 else '')
            )
        return "No response data"
    gateway_response_display.short_description = 'Gateway Response'
    
    def payment_actions(self, obj):
        actions = []
        
        if obj.is_pi_payment and obj.status == 'pending':
            confirm_url = reverse('payments:confirm_pi_payment', args=[obj.id])
            actions.append(f'<a href="{confirm_url}" class="button">Confirm Pi Payment</a>')
        
        return mark_safe(' '.join(actions))
    payment_actions.short_description = 'Actions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order', 'processed_by')


@admin.register(PiCoinRate)
class PiCoinRateAdmin(admin.ModelAdmin):
    list_display = [
        'created_at', 'pi_to_usd_display', 'source', 'is_active', 
        'change_from_previous', 'usage_count'
    ]
    list_filter = ['source', 'is_active', 'created_at']
    search_fields = ['source']
    readonly_fields = ['created_at', 'change_from_previous', 'usage_count']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Rate Information', {
            'fields': ('pi_to_usd', 'source', 'is_active')
        }),
        ('Statistics', {
            'fields': ('created_at', 'change_from_previous', 'usage_count'),
            'classes': ('collapse',)
        })
    )
    
    def pi_to_usd_display(self, obj):
        return f"${obj.pi_to_usd:.6f}"
    pi_to_usd_display.short_description = 'Pi to USD Rate'
    pi_to_usd_display.admin_order_field = 'pi_to_usd'
    
    def change_from_previous(self, obj):
        # Get the previous rate
        previous = PiCoinRate.objects.filter(
            created_at__lt=obj.created_at
        ).order_by('-created_at').first()
        
        if previous:
            change = obj.pi_to_usd - previous.pi_to_usd
            if change > 0:
                return format_html(
                    '<span style="color: green;">+${:.6f}</span>', 
                    change
                )
            elif change < 0:
                return format_html(
                    '<span style="color: red;">${:.6f}</span>', 
                    change
                )
            else:
                return "No change"
        return "First rate"
    change_from_previous.short_description = 'Change'
    
    def usage_count(self, obj):
        # Count payments using this rate
        count = Payment.objects.filter(pi_exchange_rate=obj.pi_to_usd).count()
        return f"{count} payments"
    usage_count.short_description = 'Usage'
    
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # Deactivate other rates when setting this one as active
            PiCoinRate.objects.filter(is_active=True).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(PiPaymentTransaction)
class PiPaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'pi_payment_id', 'payment_link', 'amount_pi_display', 
        'amount_usd', 'status', 'created_at', 'completed_at'
    ]
    list_filter = ['status', 'created_at', 'completed_at']
    search_fields = [
        'pi_payment_id', 'transaction_id', 'from_address', 
        'to_address', 'payment__order__id'
    ]
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': (
                'payment', 'pi_payment_id', 'transaction_id', 
                'amount_pi', 'amount_usd', 'status'
            )
        }),
        ('Addresses', {
            'fields': ('from_address', 'to_address'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('memo', 'network_fee', 'created_at', 'completed_at'),
            'classes': ('collapse',)
        })
    )
    
    def payment_link(self, obj):
        url = reverse('admin:payments_payment_change', args=[obj.payment.id])
        return format_html('<a href="{}">{}</a>', url, f'Payment #{obj.payment.id}')
    payment_link.short_description = 'Payment'
    
    def amount_pi_display(self, obj):
        return f"{obj.amount_pi:.7f} π"
    amount_pi_display.short_description = 'Pi Amount'
    amount_pi_display.admin_order_field = 'amount_pi'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment')


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
