
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Avg
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brand_logos/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    slug = models.SlugField(unique=True, blank=True, null=True)
    country_of_origin = models.CharField(max_length=100, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Brand.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    CURRENCY_CHOICES = [
        ('TZS', 'Tanzanian Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('KES', 'Kenyan Shilling'),
    ]
    
    # Store ownership (multi-vendor support)
    store = models.ForeignKey('stores.Store', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='TZS')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    stock = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_digital = models.BooleanField(default=False)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    slug = models.SlugField(unique=True, blank=True, null=True)
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        return self.compare_price and self.price < self.compare_price

    @property
    def discount_percentage(self):
        if self.compare_price and self.price < self.compare_price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def is_low_stock(self):
        return self.stock <= self.low_stock_threshold

    @property
    def average_rating(self):
        return self.reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    @property
    def review_count(self):
        return self.reviews.count()

    def __str__(self):
        return self.name



class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)  # e.g., "Size", "Color"
    value = models.CharField(max_length=100)  # e.g., "Large", "Red"
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlists')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductComparison(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comparisons')
    products = models.ManyToManyField(Product, related_name='compared_by')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comparison by {self.user.username}"


class RecentlyViewed(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_viewed')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='viewed_by')
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"


class ProductQuestion(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_questions')
    question = models.TextField()
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Question about {self.product.name}"
