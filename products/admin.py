from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Sum, Count, Avg
from .models import Product, Category, Brand, ProductImage

# Custom Admin Site Configuration
admin.site.site_header = "DoleseCommerce Administration"
admin.site.site_title = "DoleseCommerce Admin"
admin.site.index_title = "Welcome to DoleseCommerce Admin Dashboard"

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'uploaded_at')
    readonly_fields = ('uploaded_at',)
    classes = ('collapse',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'image_preview', 'name', 'formatted_price', 'category', 'brand', 
        'stock_status', 'sales_badge', 'views_count', 'is_featured', 'is_active'
    )
    list_filter = (
        'category', 'brand', 'is_active', 'is_featured', 'is_bestseller', 
        'currency', 'created_at', 'updated_at'
    )
    list_editable = ('is_active', 'is_featured')
    search_fields = ('name', 'description', 'short_description', 'sku', 'tags')
    readonly_fields = (
        'image_preview', 'sales_count', 'views_count', 'created_at', 
        'updated_at', 'profit_margin', 'stock_value'
    )
    list_per_page = 25
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'short_description', 'description', 'category', 'brand'),
            'classes': ('wide',)
        }),
        ('Pricing & Currency', {
            'fields': ('price', 'compare_price', 'currency', 'profit_margin'),
            'classes': ('wide',)
        }),
        ('Inventory & Sales', {
            'fields': ('stock', 'low_stock_threshold', 'sku', 'barcode', 'stock_value'),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image', 'image_preview'),
            'classes': ('wide',)
        }),
        ('Product Features', {
            'fields': ('weight', 'dimensions', 'is_digital', 'tags'),
            'classes': ('wide',)
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_featured', 'is_bestseller'),
            'classes': ('wide',)
        }),
        ('Store Information', {
            'fields': ('store',),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('sales_count', 'views_count', 'created_at', 'updated_at'),
            'classes': ('wide',)
        }),
    )
    
    inlines = [ProductImageInline]
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px; border: 2px solid #ddd;" />',
                obj.image.url
            )
        return format_html('<div style="width: 50px; height: 50px; background: #f8f9fa; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #6c757d; font-size: 12px;">No Image</div>')
    image_preview.short_description = '📷 Image'
    
    def formatted_price(self, obj):
        currency_symbols = {
            'TZS': 'TSh',
            'USD': '$',
            'EUR': '€',
            'KES': 'KSh',
            'PI': 'π'
        }
        symbol = currency_symbols.get(obj.currency, obj.currency)
        if obj.currency in ['TZS', 'KES']:
            price_str = f"{symbol} {obj.price:,.0f}"
        else:
            price_str = f"{symbol}{obj.price:,.2f}"
        
        # Add compare price if exists
        if obj.compare_price and obj.compare_price > obj.price:
            discount = ((obj.compare_price - obj.price) / obj.compare_price) * 100
            return format_html(
                '{} <small style="color: #dc3545; text-decoration: line-through;">{}</small> <span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px;">-{:.0f}%</span>',
                price_str,
                f"{symbol} {obj.compare_price:,.0f}" if obj.currency in ['TZS', 'KES'] else f"{symbol}{obj.compare_price:,.2f}",
                discount
            )
        return price_str
    formatted_price.short_description = '💰 Price'
    formatted_price.admin_order_field = 'price'
    
    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">OUT OF STOCK</span>')
        elif obj.stock <= obj.low_stock_threshold:
            return format_html('<span style="background: #fd7e14; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">LOW STOCK ({} left)</span>', obj.stock)
        else:
            return format_html('<span style="background: #198754; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">IN STOCK ({})</span>', obj.stock)
    stock_status.short_description = '📦 Stock Status'
    
    def sales_badge(self, obj):
        if obj.is_bestseller:
            return format_html('<span style="background: #ffc107; color: #000; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">🏆 BESTSELLER</span>')
        elif obj.sales_count > 10:
            return format_html('<span style="background: #20c997; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">🔥 {} SOLD</span>', obj.sales_count)
        elif obj.sales_count > 0:
            return format_html('<span style="background: #6f42c1; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">{} SOLD</span>', obj.sales_count)
        return format_html('<span style="background: #6c757d; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">NEW</span>')
    sales_badge.short_description = '🏷️ Sales'
    
    def profit_margin(self, obj):
        if obj.compare_price and obj.compare_price > obj.price:
            profit = obj.compare_price - obj.price
            margin = (profit / obj.compare_price) * 100
            return format_html('${:.2f} ({:.1f}%)', profit, margin)
        return "N/A"
    profit_margin.short_description = 'Profit Margin'
    
    def stock_value(self, obj):
        value = obj.stock * obj.price
        return f"${value:,.2f}"
    stock_value.short_description = 'Stock Value'
    
    actions = ['mark_as_featured', 'mark_as_not_featured', 'mark_as_active', 'mark_as_inactive']
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f"{queryset.count()} products marked as featured.")
    mark_as_featured.short_description = "⭐ Mark selected products as featured"
    
    def mark_as_not_featured(self, request, queryset):
        queryset.update(is_featured=False)
        self.message_user(request, f"{queryset.count()} products removed from featured.")
    mark_as_not_featured.short_description = "Remove from featured"
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} products activated.")
    mark_as_active.short_description = "✅ Activate selected products"
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} products deactivated.")
    mark_as_inactive.short_description = "❌ Deactivate selected products"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'product_count', 'featured_products')
    search_fields = ('name', 'description')
    readonly_fields = ('product_count',)
    list_per_page = 20
    ordering = ('name',)
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'description'),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('product_count',),
            'classes': ('wide',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        active_count = obj.products.filter(is_active=True).count()
        return format_html(
            '<span style="background: #0d6efd; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px;">{} Total</span>'
            '<span style="background: #198754; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{} Active</span>',
            count, active_count
        )
    product_count.short_description = '📊 Products'
    
    def featured_products(self, obj):
        featured = obj.products.filter(is_featured=True).count()
        if featured > 0:
            return format_html('<span style="background: #ffc107; color: #000; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">⭐ {} Featured</span>', featured)
        return format_html('<span style="color: #6c757d; font-size: 11px;">No featured products</span>')
    featured_products.short_description = '⭐ Featured'

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_of_origin', 'product_count', 'total_sales')
    list_filter = ('country_of_origin',)
    search_fields = ('name', 'description', 'country_of_origin')
    readonly_fields = ('product_count', 'total_sales')
    list_per_page = 20
    ordering = ('name',)
    
    fieldsets = (
        ('Brand Information', {
            'fields': ('name', 'description', 'country_of_origin', 'website'),
            'classes': ('wide',)
        }),
        ('Statistics', {
            'fields': ('product_count', 'total_sales'),
            'classes': ('wide',)
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        active_count = obj.products.filter(is_active=True).count()
        return format_html(
            '<span style="background: #0d6efd; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px;">{} Total</span>'
            '<span style="background: #198754; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px;">{} Active</span>',
            count, active_count
        )
    product_count.short_description = '📊 Products'
    
    def total_sales(self, obj):
        total = obj.products.aggregate(total_sales=Sum('sales_count'))['total_sales'] or 0
        if total > 0:
            return format_html('<span style="background: #20c997; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;">🔥 {} Sales</span>', total)
        return format_html('<span style="color: #6c757d; font-size: 11px;">No sales yet</span>')
    total_sales.short_description = '💰 Total Sales'
