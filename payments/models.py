from django.db import models
from django.contrib.auth.models import User
from orders.models import Order
from decimal import Decimal
import json

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('crypto', 'Cryptocurrency'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional metadata
    gateway_response = models.TextField(blank=True, help_text="Raw gateway response")
    failure_reason = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_method', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"
    
    def get_gateway_response_data(self):
        if self.gateway_response:
            try:
                return json.loads(self.gateway_response)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_gateway_response_data(self, data):
        self.gateway_response = json.dumps(data, indent=2)


class MpesaB2CTransaction(models.Model):
    """Model for Business to Customer M-Pesa transactions (sending money to customers)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='mpesa_b2c_transactions', null=True, blank=True)
    conversation_id = models.CharField(max_length=255, unique=True)
    originator_conversation_id = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.CharField(max_length=255)
    occasion = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    response_code = models.CharField(max_length=10, blank=True)
    response_description = models.TextField(blank=True)
    transaction_id = models.CharField(max_length=255, blank=True)
    transaction_receipt = models.CharField(max_length=255, blank=True)
    b2c_charges_paid_account_available_funds = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receiver_party_public_name = models.CharField(max_length=255, blank=True)
    transaction_completed_date_time = models.DateTimeField(null=True, blank=True)
    b2c_utility_account_available_funds = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    b2c_working_account_available_funds = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "M-Pesa B2C Transaction"
        verbose_name_plural = "M-Pesa B2C Transactions"
    
    def __str__(self):
        return f"B2C to {self.phone_number} - KES {self.amount} ({self.status})"
    
    @property
    def formatted_phone(self):
        """Return formatted phone number for display"""
        if self.phone_number.startswith('254'):
            return f"+{self.phone_number}"
        return self.phone_number
    
    def is_successful(self):
        return self.status == 'completed' and self.response_code == '0'


class MpesaC2BTransaction(models.Model):
    """Model for Customer to Business M-Pesa transactions (STK Push)"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='mpesa_c2b_transactions')
    checkout_request_id = models.CharField(max_length=255, unique=True)
    merchant_request_id = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=255)
    transaction_desc = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result_code = models.CharField(max_length=10, blank=True)
    result_desc = models.TextField(blank=True)
    mpesa_receipt_number = models.CharField(max_length=255, blank=True)
    transaction_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "M-Pesa C2B Transaction"
        verbose_name_plural = "M-Pesa C2B Transactions"
    
    def __str__(self):
        return f"C2B from {self.phone_number} - KES {self.amount} ({self.status})"
    
    @property
    def formatted_phone(self):
        """Return formatted phone number for display"""
        if self.phone_number.startswith('254'):
            return f"+{self.phone_number}"
        return self.phone_number
    
    def is_successful(self):
        return self.status == 'completed' and self.result_code == '0'


class PhonePayment(models.Model):
    """Model for direct phone number payments (both incoming and outgoing)"""
    PAYMENT_TYPE_CHOICES = [
        ('send', 'Send Money'),
        ('receive', 'Receive Money'),
        ('refund', 'Refund'),
        ('commission', 'Commission Payment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PROVIDER_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('airtel', 'Airtel Money'),
        ('tkash', 'T-Kash'),
    ]
    
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='mpesa')
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=255, blank=True)
    initiated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Related transactions
    mpesa_b2c = models.OneToOneField(MpesaB2CTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    mpesa_c2b = models.OneToOneField(MpesaC2BTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Phone Payment"
        verbose_name_plural = "Phone Payments"
    
    def __str__(self):
        action = "to" if self.payment_type == 'send' else "from"
        return f"{self.get_payment_type_display()} {action} {self.phone_number} - KES {self.amount}"
    
    @property
    def formatted_phone(self):
        """Return formatted phone number for display"""
        if self.phone_number.startswith('254'):
            return f"+{self.phone_number}"
        return self.phone_number
    
    def generate_reference(self):
        """Generate unique reference for the payment"""
        import uuid
        prefix = f"{self.payment_type.upper()}{self.provider.upper()}"
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)
