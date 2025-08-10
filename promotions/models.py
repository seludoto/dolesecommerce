from django.db import models
from django.contrib.auth.models import User
from products.models import Product, Category


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    usage_per_user = models.PositiveIntegerField(default=1)
    usage_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    applicable_products = models.ManyToManyField(Product, blank=True)
    applicable_categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_to and
            (self.usage_limit is None or self.usage_count < self.usage_limit)
        )


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('buy_x_get_y', 'Buy X Get Y'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_quantity = models.PositiveIntegerField(default=1)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class FlashSale(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    products = models.ManyToManyField(Product, through='FlashSaleProduct')
    discount_percentage = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_quantity_per_user = models.PositiveIntegerField(default=1)
    image = models.ImageField(upload_to='flash_sales/', blank=True)
    featured = models.BooleanField(default=False, help_text="Show on homepage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    @property
    def is_live(self):
        from django.utils import timezone
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time
    
    @property
    def time_remaining(self):
        from django.utils import timezone
        if not self.is_live:
            return None
        return self.end_time - timezone.now()
    
    @property
    def total_stock(self):
        return sum(product.stock_limit for product in self.flashsaleproduct_set.all())
    
    @property
    def total_sold(self):
        return sum(product.sold_count for product in self.flashsaleproduct_set.all())
    
    @property
    def progress_percentage(self):
        total_stock = self.total_stock
        if total_stock == 0:
            return 0
        return min((self.total_sold / total_stock) * 100, 100)


class FlashSaleProduct(models.Model):
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_limit = models.PositiveIntegerField()
    sold_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['flash_sale', 'product']


class LoyaltyProgram(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    points_per_dollar = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    min_points_to_redeem = models.PositiveIntegerField(default=100)
    points_expiry_days = models.PositiveIntegerField(default=365)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserLoyalty(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='loyalty')
    points = models.PositiveIntegerField(default=0)
    tier = models.CharField(max_length=20, default='Bronze')
    lifetime_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    referrals_made = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.tier} ({self.points} points)"


class PromotionRule(models.Model):
    RULE_TYPE_CHOICES = [
        ('cart_total', 'Cart Total'),
        ('product_quantity', 'Product Quantity'),
        ('user_group', 'User Group'),
        ('first_purchase', 'First Purchase'),
        ('seasonal', 'Seasonal'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    condition_data = models.JSONField(default=dict)
    action_data = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    priority = models.PositiveIntegerField(default=0)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return self.name


class PointTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('expired', 'Points Expired'),
        ('bonus', 'Bonus Points'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='point_transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    points = models.IntegerField()
    description = models.CharField(max_length=255)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.points} points ({self.transaction_type})"


class Wishlist(models.Model):
    """User wishlist similar to KiKUU's wishlist"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wishlist"
    
    @property
    def total_items(self):
        return self.items.count()


class WishlistItem(models.Model):
    """Items in user's wishlist"""
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('wishlist', 'product')
    
    def __str__(self):
        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"


class UserNotification(models.Model):
    """User notifications system"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=[
            ('ORDER', 'Order Update'),
            ('PROMOTION', 'Promotion'),
            ('FLASH_SALE', 'Flash Sale'),
            ('SYSTEM', 'System'),
            ('REVIEW', 'Review Request'),
        ],
        default='SYSTEM'
    )
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, help_text="URL to redirect when notification is clicked")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} for {self.user.username}"


class InviteFriend(models.Model):
    """Friend invitation system"""
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    email = models.EmailField()
    invitation_code = models.CharField(max_length=50, unique=True)
    invited_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_invitations')
    is_accepted = models.BooleanField(default=False)
    reward_claimed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.inviter.username} invited {self.email}"
    
    def generate_invitation_code(self):
        import uuid
        self.invitation_code = str(uuid.uuid4()).replace('-', '')[:10].upper()
        return self.invitation_code


class FlashSalePurchase(models.Model):
    """Track customer purchases in flash sales"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    flash_sale_product = models.ForeignKey(FlashSaleProduct, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        user_info = self.user.username if self.user else f"Session {self.session_key}"
        return f"{user_info} bought {self.quantity}x {self.flash_sale_product.product.name}"
