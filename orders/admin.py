from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Count
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_item_total',)
    fields = ('product', 'quantity', 'price', 'get_item_total')
    
    def get_item_total(self, obj):
        if obj.pk:
            total = obj.quantity * obj.price
            return format_html('<strong>TZS {:,.2f}</strong>', total)
        return '-'
    get_item_total.short_description = 'Total'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('get_order_number', 'get_customer', 'get_order_status', 'get_items_count', 'get_order_total', 'created_at')
    list_filter = ('is_paid', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'shipping_address', 'id')
    readonly_fields = ('created_at', 'updated_at', 'get_order_summary', 'get_customer_info')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('get_order_summary', 'is_paid')
        }),
        ('Customer Details', {
            'fields': ('get_customer_info', 'shipping_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_order_number(self, obj):
        """Display formatted order number"""
        return format_html(
            '<span class="badge bg-primary" style="font-size: 12px;">#{:05d}</span>',
            obj.id
        )
    get_order_number.short_description = 'Order #'
    
    def get_customer(self, obj):
        """Display customer with link"""
        full_name = obj.user.get_full_name() or obj.user.username
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br><small class="text-muted">{}</small>',
            reverse('admin:auth_user_change', args=[obj.user.pk]),
            full_name,
            obj.user.email
        )
    get_customer.short_description = 'Customer'
    
    def get_order_status(self, obj):
        """Display order status with badges"""
        status_badges = []
        
        if obj.is_paid:
            status_badges.append('<span class="badge bg-success">💳 Paid</span>')
        else:
            status_badges.append('<span class="badge bg-warning">⏳ Pending Payment</span>')
            
        # Check if order is recent (within 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        if obj.created_at > timezone.now() - timedelta(hours=24):
            status_badges.append('<span class="badge bg-info">🆕 New</span>')
            
        return mark_safe(' '.join(status_badges))
    get_order_status.short_description = 'Status'
    
    def get_items_count(self, obj):
        """Display number of items in order"""
        count = obj.items.count()
        total_quantity = obj.items.aggregate(total=Sum('quantity'))['total'] or 0
        
        return format_html(
            '<span class="badge bg-secondary">{} items</span><br><small>{} total qty</small>',
            count, total_quantity
        )
    get_items_count.short_description = 'Items'
    
    def get_order_total(self, obj):
        """Calculate and display order total"""
        total = sum(item.quantity * item.price for item in obj.items.all())
        
        if total > 0:
            # Color code based on order value
            if total >= 100000:  # 100K TZS
                color = 'success'
            elif total >= 50000:  # 50K TZS
                color = 'primary'
            else:
                color = 'secondary'
                
            return format_html(
                '<span class="badge bg-{} fs-6">TZS {:,.2f}</span>',
                color, total
            )
        return format_html('<span class="text-muted">TZS 0.00</span>')
    get_order_total.short_description = 'Total Amount'
    
    def get_order_summary(self, obj):
        """Display comprehensive order summary"""
        if obj.pk:
            items_count = obj.items.count()
            total_amount = sum(item.quantity * item.price for item in obj.items.all())
            
            summary = f"""
            <div class="card" style="max-width: 400px;">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">📋 Order #{obj.id:05d}</h6>
                </div>
                <div class="card-body">
                    <p><strong>Items:</strong> {items_count}</p>
                    <p><strong>Total Amount:</strong> TZS {total_amount:,.2f}</p>
                    <p><strong>Status:</strong> {'✅ Paid' if obj.is_paid else '⏳ Pending Payment'}</p>
                    <p><strong>Date:</strong> {obj.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
            """
            return mark_safe(summary)
        return '-'
    get_order_summary.short_description = 'Order Summary'
    
    def get_customer_info(self, obj):
        """Display customer information card"""
        profile_link = reverse('admin:auth_user_change', args=[obj.user.pk])
        
        info = f"""
        <div class="card" style="max-width: 400px;">
            <div class="card-header bg-info text-white">
                <h6 class="mb-0">👤 Customer Information</h6>
            </div>
            <div class="card-body">
                <p><strong>Name:</strong> {obj.user.get_full_name() or obj.user.username}</p>
                <p><strong>Email:</strong> {obj.user.email}</p>
                <p><strong>Username:</strong> {obj.user.username}</p>
                <p><strong>Member Since:</strong> {obj.user.date_joined.strftime('%B %Y')}</p>
                <a href="{profile_link}" class="btn btn-outline-primary btn-sm">View Full Profile</a>
            </div>
        </div>
        """
        return mark_safe(info)
    get_customer_info.short_description = 'Customer Details'
    
    actions = ['mark_as_paid', 'mark_as_unpaid']
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(is_paid=True)
        self.message_user(request, f'{updated} orders were marked as paid.')
    mark_as_paid.short_description = "💳 Mark selected orders as paid"
    
    def mark_as_unpaid(self, request, queryset):
        updated = queryset.update(is_paid=False)
        self.message_user(request, f'{updated} orders were marked as unpaid.')
    mark_as_unpaid.short_description = "⏳ Mark selected orders as unpaid"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('get_order_link', 'get_product_info', 'quantity', 'price', 'get_item_total')
    list_filter = ('order__is_paid', 'order__created_at')
    search_fields = ('order__id', 'product__name', 'product__sku')
    readonly_fields = ('get_item_total', 'get_order_info', 'get_product_details')
    ordering = ('-order__created_at',)
    
    fieldsets = (
        ('Order Information', {
            'fields': ('get_order_info',)
        }),
        ('Product Information', {
            'fields': ('get_product_details', 'product')
        }),
        ('Pricing Details', {
            'fields': ('quantity', 'price', 'get_item_total')
        }),
    )
    
    def get_order_link(self, obj):
        """Display order link"""
        return format_html(
            '<a href="{}" class="text-decoration-none">Order #{:05d}</a>',
            reverse('admin:orders_order_change', args=[obj.order.pk]),
            obj.order.id
        )
    get_order_link.short_description = 'Order'
    
    def get_product_info(self, obj):
        """Display product information"""
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br><small class="text-muted">SKU: {}</small>',
            reverse('admin:products_product_change', args=[obj.product.pk]),
            obj.product.name,
            obj.product.sku or 'N/A'
        )
    get_product_info.short_description = 'Product'
    
    def get_item_total(self, obj):
        """Calculate item total"""
        if obj.pk:
            total = obj.quantity * obj.price
            return format_html('<strong class="text-success">TZS {:,.2f}</strong>', total)
        return '-'
    get_item_total.short_description = 'Total'
    
    def get_order_info(self, obj):
        """Display order information"""
        if obj.pk:
            order = obj.order
            return format_html(
                '''
                <div class="alert alert-info">
                    <h6>📋 Order #{:05d}</h6>
                    <p><strong>Customer:</strong> {}</p>
                    <p><strong>Status:</strong> {}</p>
                    <p><strong>Date:</strong> {}</p>
                    <a href="{}" class="btn btn-primary btn-sm">View Full Order</a>
                </div>
                ''',
                order.id,
                order.user.get_full_name() or order.user.username,
                'Paid' if order.is_paid else 'Pending Payment',
                order.created_at.strftime('%B %d, %Y'),
                reverse('admin:orders_order_change', args=[order.pk])
            )
        return '-'
    get_order_info.short_description = 'Order Details'
    
    def get_product_details(self, obj):
        """Display product details"""
        if obj.pk:
            product = obj.product
            return format_html(
                '''
                <div class="alert alert-secondary">
                    <h6>📦 {}</h6>
                    <p><strong>SKU:</strong> {}</p>
                    <p><strong>Brand:</strong> {}</p>
                    <p><strong>Category:</strong> {}</p>
                    <p><strong>Stock:</strong> {}</p>
                    <a href="{}" class="btn btn-secondary btn-sm">View Product</a>
                </div>
                ''',
                product.name,
                product.sku or 'N/A',
                product.brand.name if product.brand else 'N/A',
                product.category.name if product.category else 'N/A',
                f'{product.stock_quantity} units' if hasattr(product, 'stock_quantity') else 'N/A',
                reverse('admin:products_product_change', args=[product.pk])
            )
        return '-'
    get_product_details.short_description = 'Product Information'
