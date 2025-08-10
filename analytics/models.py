from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from orders.models import Order
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import json


class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('view_product', 'Viewed Product'),
        ('add_to_cart', 'Added to Cart'),
        ('remove_from_cart', 'Removed from Cart'),
        ('purchase', 'Made Purchase'),
        ('search', 'Searched'),
        ('login', 'Logged In'),
        ('register', 'Registered'),
        ('add_to_wishlist', 'Added to Wishlist'),
        ('share_product', 'Shared Product'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    search_query = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} - {self.timestamp}"


class ProductAnalytics(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='analytics')
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    total_cart_adds = models.PositiveIntegerField(default=0)
    total_purchases = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    bounce_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_time_on_page = models.DurationField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.product.name}"


class SalesReport(models.Model):
    date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.PositiveIntegerField(default=0)
    total_customers = models.PositiveIntegerField(default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    top_selling_product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['date']
        ordering = ['-date']

    def __str__(self):
        return f"Sales Report - {self.date}"


class SearchAnalytics(models.Model):
    query = models.CharField(max_length=255)
    results_count = models.PositiveIntegerField(default=0)
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    search_count = models.PositiveIntegerField(default=1)
    last_searched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['query']

    def __str__(self):
        return self.query


# New Advanced Analytics Models

class SearchQuery(models.Model):
    """Track search queries for analytics"""
    query = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    filters = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
            models.Index(fields=['results_count']),
        ]
    
    def __str__(self):
        return f"{self.query} ({self.results_count} results)"


class UserInteraction(models.Model):
    """Track user interactions with products"""
    INTERACTION_TYPES = [
        ('view', 'Product View'),
        ('click', 'Product Click'),
        ('add_to_cart', 'Add to Cart'),
        ('remove_from_cart', 'Remove from Cart'),
        ('add_to_wishlist', 'Add to Wishlist'),
        ('remove_from_wishlist', 'Remove from Wishlist'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('share', 'Share'),
        ('compare', 'Compare'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    session_id = models.CharField(max_length=40, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['interaction_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.interaction_type} {self.product.name}"


class ConversionFunnel(models.Model):
    """Track conversion funnel analytics"""
    FUNNEL_STAGES = [
        ('homepage', 'Homepage Visit'),
        ('category', 'Category Browse'),
        ('product_view', 'Product View'),
        ('add_to_cart', 'Add to Cart'),
        ('checkout_start', 'Checkout Started'),
        ('payment_info', 'Payment Info Added'),
        ('purchase', 'Purchase Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=40)
    stage = models.CharField(max_length=20, choices=FUNNEL_STAGES)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['stage', 'timestamp']),
        ]


class ABTest(models.Model):
    """A/B Testing framework"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    traffic_allocation = models.FloatField(default=0.5)  # 0.0 to 1.0
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class BusinessMetric(models.Model):
    """Store business metrics for dashboard"""
    METRIC_TYPES = [
        ('revenue', 'Revenue'),
        ('orders', 'Orders'),
        ('users', 'Users'),
        ('conversion_rate', 'Conversion Rate'),
        ('avg_order_value', 'Average Order Value'),
        ('customer_lifetime_value', 'Customer Lifetime Value'),
        ('bounce_rate', 'Bounce Rate'),
        ('page_views', 'Page Views'),
        ('cart_abandonment', 'Cart Abandonment Rate'),
    ]
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['metric_type', 'date']
        ordering = ['-date', 'metric_type']
        indexes = [
            models.Index(fields=['metric_type', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} on {self.date}"
