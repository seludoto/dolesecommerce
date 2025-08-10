from django.contrib import admin
from .models import Coupon, Discount, FlashSale, LoyaltyProgram, PromotionRule, FlashSaleProduct


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'is_active', 'usage_count', 'usage_limit', 'valid_from', 'valid_to']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_to']
    search_fields = ['code', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'min_order_amount', 'max_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_per_user', 'usage_count')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to', 'is_active')
        }),
        ('Restrictions', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def activate_coupons(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupons were activated.')
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupons were deactivated.')
    deactivate_coupons.short_description = "Deactivate selected coupons"


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'discount_value', 'is_active', 'start_date', 'end_date']
    list_filter = ['discount_type', 'is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Discount Information', {
            'fields': ('name', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'min_quantity', 'max_discount_amount')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date', 'is_active')
        }),
        ('Applicable Items', {
            'fields': ('products', 'categories'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class FlashSaleProductInline(admin.TabularInline):
    model = FlashSaleProduct
    extra = 1
    fields = ['product', 'sale_price', 'stock_limit', 'sold_count']
    readonly_fields = ['sold_count']


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percentage', 'is_active', 'start_time', 'end_time', 'products_count']
    list_filter = ['is_active', 'start_time', 'end_time']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [FlashSaleProductInline]
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products Count'
    
    fieldsets = (
        ('Flash Sale Information', {
            'fields': ('name', 'description')
        }),
        ('Sale Settings', {
            'fields': ('discount_percentage', 'max_quantity_per_user')
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_per_dollar', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Program Information', {
            'fields': ('name', 'description')
        }),
        ('Points System', {
            'fields': ('points_per_dollar', 'min_points_to_redeem', 'points_expiry_days')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PromotionRule)
class PromotionRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'rule_type', 'is_active', 'priority', 'created_at']
    list_filter = ['rule_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Rule Information', {
            'fields': ('name', 'description', 'rule_type')
        }),
        ('Conditions', {
            'fields': ('condition_data',)
        }),
        ('Actions', {
            'fields': ('action_data',)
        }),
        ('Settings', {
            'fields': ('is_active', 'priority', 'start_date', 'end_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
