from django.contrib import admin
from django.utils import timezone
from .models import (
    Cart, CartItem, SavedForLater, PromoCode, CartPromoCode, 
    AbandonedCart, CartRecommendation
)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'total_items', 'total_price', 'is_abandoned', 'created_at']
    list_filter = ['is_abandoned', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'session_key']
    readonly_fields = ['total_items', 'total_price', 'created_at', 'updated_at']
    
    def total_items(self, obj):
        return obj.total_items
    total_items.short_description = 'Total Items'
    
    def total_price(self, obj):
        return f"${obj.total_price:.2f}"
    total_price.short_description = 'Total Price'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity', 'size', 'color', 'total_price', 'added_at']
    list_filter = ['added_at', 'size', 'color']
    search_fields = ['product__name', 'cart__user__username']
    readonly_fields = ['total_price', 'added_at', 'updated_at']
    
    def total_price(self, obj):
        return f"${obj.total_price:.2f}"
    total_price.short_description = 'Total Price'


@admin.register(SavedForLater)
class SavedForLaterAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'size', 'color', 'saved_at']
    list_filter = ['saved_at', 'size', 'color']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['saved_at']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'description', 'discount_type', 'discount_value', 
        'minimum_order', 'is_active', 'used_count', 'usage_limit', 'valid_until'
    ]
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until', 'first_time_users_only']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'maximum_discount', 'minimum_order')
        }),
        ('Validity & Usage', {
            'fields': ('valid_from', 'valid_until', 'usage_limit', 'used_count', 'first_time_users_only')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )


@admin.register(CartPromoCode)
class CartPromoCodeAdmin(admin.ModelAdmin):
    list_display = ['cart', 'promo_code', 'discount_amount', 'applied_at']
    list_filter = ['applied_at', 'promo_code__discount_type']
    search_fields = ['cart__user__username', 'promo_code__code']
    readonly_fields = ['applied_at']
    
    def discount_amount(self, obj):
        return f"${obj.discount_amount:.2f}"


@admin.register(AbandonedCart)
class AbandonedCartAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'total_value', 'email_sent', 'recovered', 
        'created_at', 'email_sent_at', 'recovered_at'
    ]
    list_filter = ['email_sent', 'recovered', 'created_at']
    search_fields = ['user__username', 'user__email', 'session_key']
    readonly_fields = ['created_at', 'email_sent_at', 'recovered_at']
    
    def user_email(self, obj):
        if obj.user:
            return obj.user.email
        return 'Anonymous'
    user_email.short_description = 'User Email'
    
    def total_value(self, obj):
        return f"${obj.total_value:.2f}"
    total_value.short_description = 'Total Value'


@admin.register(CartRecommendation)
class CartRecommendationAdmin(admin.ModelAdmin):
    list_display = ['cart', 'recommended_product', 'recommendation_type', 'confidence_score', 'created_at']
    list_filter = ['recommendation_type', 'created_at']
    search_fields = ['cart__user__username', 'recommended_product__name']
    readonly_fields = ['created_at']


# Custom admin actions
def mark_carts_as_abandoned(modeladmin, request, queryset):
    """Mark selected carts as abandoned"""
    for cart in queryset:
        cart.mark_abandoned()
    modeladmin.message_user(request, f"Marked {queryset.count()} carts as abandoned.")

mark_carts_as_abandoned.short_description = "Mark selected carts as abandoned"

# Add the action to CartAdmin
CartAdmin.actions = [mark_carts_as_abandoned]


def send_abandoned_cart_emails(modeladmin, request, queryset):
    """Send recovery emails for abandoned carts"""
    count = 0
    for abandoned_cart in queryset.filter(email_sent=False, user__isnull=False):
        # Here you would integrate with your email system
        # For now, just mark as email sent
        abandoned_cart.email_sent = True
        abandoned_cart.email_sent_at = timezone.now()
        abandoned_cart.save()
        count += 1
    
    modeladmin.message_user(request, f"Sent recovery emails for {count} abandoned carts.")

send_abandoned_cart_emails.short_description = "Send recovery emails"

# Add the action to AbandonedCartAdmin
AbandonedCartAdmin.actions = [send_abandoned_cart_emails]
