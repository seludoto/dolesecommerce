from django.db import models
from orders.models import Order

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # Pi Coin fields
    pi_payment_id = models.CharField(max_length=100, blank=True)
    pi_wallet_address = models.CharField(max_length=200, blank=True)
    pi_status = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} - {self.status}"
