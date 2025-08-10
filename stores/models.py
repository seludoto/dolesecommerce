from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

class Store(models.Model):
    """Model for seller stores/shops"""
    STORE_STATUS_CHOICES = [
        ('pending', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ]
    
    STORE_TYPE_CHOICES = [
        ('individual', 'Individual Seller'),
        ('business', 'Business'),
        ('brand', 'Brand Store'),
        ('wholesaler', 'Wholesaler'),
    ]
    
    # Basic Information
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store')
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    
    # Store Details
    store_type = models.CharField(max_length=20, choices=STORE_TYPE_CHOICES, default='individual')
    status = models.CharField(max_length=20, choices=STORE_STATUS_CHOICES, default='pending')
    
    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    
    # Business Information
    business_license = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=100, blank=True)
    
    # Store Settings
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    return_policy = models.TextField(blank=True)
    shipping_policy = models.TextField(blank=True)
    
    # Commission and Fees
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                        validators=[MinValueValidator(0), MaxValueValidator(50)])
    
    # Store Performance
    total_sales = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0,
                                validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.PositiveIntegerField(default=0)
    
    # Social Media
    website = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Store"
        verbose_name_plural = "Stores"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Store.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('stores:store_detail', kwargs={'slug': self.slug})
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def product_count(self):
        return self.products.filter(is_active=True).count()
    
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0


class StoreCategory(models.Model):
    """Categories that stores can belong to"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome icon class
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Store Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class StoreReview(models.Model):
    """Reviews for stores"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    review = models.TextField()
    is_verified = models.BooleanField(default=False)  # If user actually bought from store
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['store', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.store.name} - {self.rating} stars by {self.user.username}"


class StoreApplication(models.Model):
    """Model for store applications"""
    APPLICATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review'),
    ]
    
    # Applicant Information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_applications')
    store_name = models.CharField(max_length=200)
    store_description = models.TextField()
    
    # Business Information
    business_type = models.CharField(max_length=20, choices=Store.STORE_TYPE_CHOICES)
    business_license = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    business_address = models.TextField()
    
    # Documents
    license_document = models.FileField(upload_to='store_applications/licenses/', blank=True)
    tax_document = models.FileField(upload_to='store_applications/tax/', blank=True)
    identity_document = models.FileField(upload_to='store_applications/identity/', blank=True)
    
    # Application Status
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='reviewed_applications')
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Application for {self.store_name} by {self.user.username}"


class StoreSubscription(models.Model):
    """Store subscription plans"""
    PLAN_CHOICES = [
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
        ('enterprise', 'Enterprise Plan'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    store = models.OneToOneField(Store, on_delete=models.CASCADE, related_name='subscription')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    
    # Plan Features
    max_products = models.PositiveIntegerField(default=100)
    max_images_per_product = models.PositiveIntegerField(default=5)
    commission_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    priority_support = models.BooleanField(default=False)
    analytics_access = models.BooleanField(default=False)
    
    # Billing
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    yearly_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.store.name} - {self.plan.title()} Plan"


class StoreAnalytics(models.Model):
    """Store analytics and performance data"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='analytics')
    date = models.DateField()
    
    # Sales Metrics
    daily_sales = models.PositiveIntegerField(default=0)
    daily_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    daily_orders = models.PositiveIntegerField(default=0)
    
    # Traffic Metrics
    page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    product_views = models.PositiveIntegerField(default=0)
    
    # Conversion Metrics
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['store', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.store.name} analytics for {self.date}"


class StoreNotification(models.Model):
    """Notifications for store owners"""
    NOTIFICATION_TYPES = [
        ('order', 'New Order'),
        ('review', 'New Review'),
        ('message', 'New Message'),
        ('system', 'System Notification'),
        ('payment', 'Payment Update'),
    ]
    
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.store.name}: {self.title}"


class StoreFollower(models.Model):
    """Users following stores"""
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_stores')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['store', 'user']
    
    def __str__(self):
        return f"{self.user.username} follows {self.store.name}"
