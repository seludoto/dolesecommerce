from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from decimal import Decimal
from django.utils import timezone


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_abandoned = models.BooleanField(default=False)
    abandoned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Cart {self.id}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def subtotal(self):
        return self.total_price

    @property
    def shipping_cost(self):
        # Free shipping over $100
        if self.total_price >= 100:
            return Decimal('0.00')
        return Decimal('5.00')

    @property
    def tax_amount(self):
        return self.subtotal * Decimal('0.08')  # 8% tax

    @property
    def final_total(self):
        total = self.subtotal + self.shipping_cost + self.tax_amount
        # Apply promo code discounts
        for promo in self.applied_promos.all():
            total -= promo.discount_amount
        return total

    def mark_abandoned(self):
        """Mark cart as abandoned after certain time of inactivity"""
        self.is_abandoned = True
        self.abandoned_at = timezone.now()
        self.save()

    def clear_cart(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=30, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'size', 'color']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.product.price * self.quantity

    @property
    def savings(self):
        """Calculate savings if there's a compare price"""
        if hasattr(self.product, 'compare_price') and self.product.compare_price:
            return (self.product.compare_price - self.product.price) * self.quantity
        return Decimal('0.00')


class SavedForLater(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=30, blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product', 'size', 'color']

    def __str__(self):
        return f"{self.user.username} saved {self.product.name}"


class PromoCode(models.Model):
    """Promotional codes for discounts"""
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200)
    discount_type = models.CharField(
        max_length=15,
        choices=[
            ('PERCENTAGE', 'Percentage'),
            ('FIXED', 'Fixed Amount'),
            ('FREE_SHIPPING', 'Free Shipping'),
            ('BOGO', 'Buy One Get One'),
        ],
        default='PERCENTAGE'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maximum_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    first_time_users_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.description}"

    @property
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.usage_limit is None or self.used_count < self.usage_limit)
        )

    def calculate_discount(self, cart_total):
        """Calculate discount amount based on cart total"""
        if not self.is_valid or cart_total < self.minimum_order:
            return Decimal('0.00')

        discount = Decimal('0.00')
        
        if self.discount_type == 'PERCENTAGE':
            discount = cart_total * (self.discount_value / 100)
            if self.maximum_discount:
                discount = min(discount, self.maximum_discount)
        elif self.discount_type == 'FIXED':
            discount = min(self.discount_value, cart_total)
        elif self.discount_type == 'FREE_SHIPPING':
            discount = Decimal('5.00')  # Shipping cost
            
        return discount


class CartPromoCode(models.Model):
    """Applied promo codes to carts"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='applied_promos')
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'promo_code')

    def __str__(self):
        return f"{self.promo_code.code} applied to cart {self.cart.id}"


class AbandonedCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    cart_data = models.JSONField()
    total_value = models.DecimalField(max_digits=10, decimal_places=2)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    recovered = models.BooleanField(default=False)
    recovered_at = models.DateTimeField(null=True, blank=True)
    recovery_token = models.CharField(max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Abandoned cart - {self.created_at}"

    def generate_recovery_link(self):
        """Generate a unique recovery link for the abandoned cart"""
        import uuid
        self.recovery_token = str(uuid.uuid4()).replace('-', '')
        self.save()
        return f"/cart/recover/{self.recovery_token}/"


class CartRecommendation(models.Model):
    """Store AI-powered cart recommendations"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='recommendations')
    recommended_product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommendation_type = models.CharField(
        max_length=20,
        choices=[
            ('FREQUENTLY_BOUGHT', 'Frequently Bought Together'),
            ('SIMILAR', 'Similar Products'),
            ('TRENDING', 'Trending Now'),
            ('RECENTLY_VIEWED', 'Recently Viewed'),
            ('CATEGORY_BASED', 'Based on Category'),
        ]
    )
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'recommended_product')

    def __str__(self):
        return f"Recommendation: {self.recommended_product.name} for cart {self.cart.id}"
