from django.db import models
from django.contrib.auth.models import User


class ShippingMethod(models.Model):
    """Different shipping methods available"""
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    estimated_days = models.PositiveIntegerField(help_text="Estimated delivery days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['estimated_days', 'name']

    def __str__(self):
        return f"{self.name} ({self.provider})"


class ShippingRate(models.Model):
    """Shipping rates based on weight and method"""
    shipping_method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE, related_name='rates')
    min_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Minimum weight in kg")
    max_weight = models.DecimalField(max_digits=8, decimal_places=2, help_text="Maximum weight in kg")
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Shipping cost")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['shipping_method', 'min_weight']
        unique_together = ['shipping_method', 'min_weight', 'max_weight']

    def __str__(self):
        return f"{self.shipping_method.name}: {self.min_weight}-{self.max_weight}kg - ${self.rate}"


class ShippingAddress(models.Model):
    """User shipping addresses"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=100)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.country}"

    def save(self, *args, **kwargs):
        # Ensure only one default address per user
        if self.is_default:
            ShippingAddress.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)


class Tracking(models.Model):
    """Package tracking information"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed_delivery', 'Failed Delivery'),
        ('returned', 'Returned'),
    ]

    order = models.OneToOneField('orders.Order', on_delete=models.CASCADE, related_name='tracking')
    tracking_number = models.CharField(max_length=50, unique=True)
    carrier = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    current_location = models.CharField(max_length=255, blank=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Tracking #{self.tracking_number} - {self.status}"


class TrackingEvent(models.Model):
    """Individual tracking events/updates"""
    tracking = models.ForeignKey(Tracking, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=20, choices=Tracking.STATUS_CHOICES)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.tracking.tracking_number} - {self.status} at {self.timestamp}"
