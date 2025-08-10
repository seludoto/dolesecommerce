from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Avg
from .models import ShippingMethod, ShippingRate, ShippingAddress, Tracking

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = [
        'get_method_info', 'get_provider_badge', 'get_delivery_time', 
        'get_rates_info', 'get_status_badge', 'get_usage_stats'
    ]
    list_filter = ['provider', 'is_active', 'created_at']
    search_fields = ['name', 'provider', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_method_statistics']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider', 'description')
        }),
        ('Service Details', {
            'fields': ('estimated_days', 'is_active')
        }),
        ('Statistics', {
            'fields': ('get_method_statistics', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_method_info(self, obj):
        """Display method name with description"""
        description = (obj.description[:50] + '...') if obj.description and len(obj.description) > 50 else obj.description
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            obj.name,
            description or 'No description'
        )
    get_method_info.short_description = 'Shipping Method'
    
    def get_provider_badge(self, obj):
        """Display provider with appropriate badge"""
        provider_colors = {
            'DHL': 'warning',
            'FedEx': 'primary',
            'UPS': 'success',
            'USPS': 'info',
            'Local': 'secondary'
        }
        color = provider_colors.get(obj.provider, 'dark')
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.provider
        )
    get_provider_badge.short_description = 'Provider'
    
    def get_delivery_time(self, obj):
        """Display estimated delivery time"""
        if obj.estimated_days:
            if obj.estimated_days == 1:
                return format_html('<span class="badge bg-success">⚡ Next Day</span>')
            elif obj.estimated_days <= 3:
                return format_html('<span class="badge bg-primary">🚀 {} Days</span>', obj.estimated_days)
            elif obj.estimated_days <= 7:
                return format_html('<span class="badge bg-warning">📦 {} Days</span>', obj.estimated_days)
            else:
                return format_html('<span class="badge bg-secondary">🐌 {} Days</span>', obj.estimated_days)
        return format_html('<span class="text-muted">Not specified</span>')
    get_delivery_time.short_description = 'Delivery Time'
    
    def get_rates_info(self, obj):
        """Display shipping rates information"""
        rates_count = obj.shipping_rates.count()
        if rates_count > 0:
            active_rates = obj.shipping_rates.filter(is_active=True).count()
            min_rate = obj.shipping_rates.aggregate(min_rate=models.Min('rate'))['min_rate']
            max_rate = obj.shipping_rates.aggregate(max_rate=models.Max('rate'))['max_rate']
            
            if min_rate and max_rate:
                if min_rate == max_rate:
                    rate_display = f'TZS {min_rate:,.2f}'
                else:
                    rate_display = f'TZS {min_rate:,.2f} - {max_rate:,.2f}'
            else:
                rate_display = 'No rates'
                
            return format_html(
                '<strong>{}</strong><br><small>{} rates ({} active)</small>',
                rate_display, rates_count, active_rates
            )
        return format_html('<span class="text-muted">No rates configured</span>')
    get_rates_info.short_description = 'Rates'
    
    def get_status_badge(self, obj):
        """Display status badge"""
        if obj.is_active:
            return format_html('<span class="badge bg-success">✅ Active</span>')
        else:
            return format_html('<span class="badge bg-danger">❌ Inactive</span>')
    get_status_badge.short_description = 'Status'
    
    def get_usage_stats(self, obj):
        """Display usage statistics"""
        # This would need to be implemented based on your tracking model
        # For now, showing a placeholder
        return format_html('<small class="text-muted">Track usage</small>')
    get_usage_stats.short_description = 'Usage'
    
    def get_method_statistics(self, obj):
        """Display comprehensive method statistics"""
        if obj.pk:
            rates_count = obj.shipping_rates.count()
            active_rates = obj.shipping_rates.filter(is_active=True).count()
            
            stats = f"""
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">📊 Shipping Method Statistics</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <p><strong>Total Rates:</strong> {rates_count}</p>
                            <p><strong>Active Rates:</strong> {active_rates}</p>
                            <p><strong>Provider:</strong> {obj.provider}</p>
                        </div>
                        <div class="col-md-6">
                            <p><strong>Estimated Delivery:</strong> {obj.estimated_days} days</p>
                            <p><strong>Status:</strong> {'Active' if obj.is_active else 'Inactive'}</p>
                            <p><strong>Created:</strong> {obj.created_at.strftime('%B %d, %Y')}</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return mark_safe(stats)
        return '-'
    get_method_statistics.short_description = 'Method Statistics'
    
    actions = ['activate_methods', 'deactivate_methods']
    
    def activate_methods(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} shipping methods were activated.')
    activate_methods.short_description = "✅ Activate selected methods"
    
    def deactivate_methods(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} shipping methods were deactivated.')
    deactivate_methods.short_description = "❌ Deactivate selected methods"

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = [
        'get_method_link', 'get_weight_range', 'get_rate_display', 
        'get_status_badge', 'get_rate_analysis'
    ]
    list_filter = ['shipping_method', 'is_active']
    search_fields = ['shipping_method__name']
    ordering = ['shipping_method__name', 'min_weight']
    
    fieldsets = (
        ('Shipping Method', {
            'fields': ('shipping_method',)
        }),
        ('Weight Configuration', {
            'fields': ('min_weight', 'max_weight')
        }),
        ('Pricing & Status', {
            'fields': ('rate', 'is_active')
        }),
    )
    
    def get_method_link(self, obj):
        """Display shipping method with link"""
        method_url = reverse('admin:shipping_shippingmethod_change', args=[obj.shipping_method.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br><small class="text-muted">{}</small>',
            method_url, obj.shipping_method.name, obj.shipping_method.provider
        )
    get_method_link.short_description = 'Shipping Method'
    
    def get_weight_range(self, obj):
        """Display weight range"""
        if obj.max_weight:
            return format_html(
                '<span class="badge bg-info">{} - {} kg</span>',
                obj.min_weight, obj.max_weight
            )
        else:
            return format_html(
                '<span class="badge bg-info">{}+ kg</span>',
                obj.min_weight
            )
    get_weight_range.short_description = 'Weight Range'
    
    def get_rate_display(self, obj):
        """Display rate with currency"""
        return format_html(
            '<strong class="text-success">TZS {:,.2f}</strong>',
            obj.rate
        )
    get_rate_display.short_description = 'Rate'
    
    def get_status_badge(self, obj):
        """Display status badge"""
        if obj.is_active:
            return format_html('<span class="badge bg-success">✅ Active</span>')
        else:
            return format_html('<span class="badge bg-danger">❌ Inactive</span>')
    get_status_badge.short_description = 'Status'
    
    def get_rate_analysis(self, obj):
        """Display rate analysis"""
        # Calculate rate per kg
        if obj.max_weight and obj.max_weight > obj.min_weight:
            avg_weight = (obj.min_weight + obj.max_weight) / 2
            rate_per_kg = obj.rate / avg_weight
            return format_html(
                '<small>~TZS {:,.2f}/kg</small>',
                rate_per_kg
            )
        return format_html('<small class="text-muted">-</small>')
    get_rate_analysis.short_description = 'Rate/kg'
    
    actions = ['activate_rates', 'deactivate_rates']
    
    def activate_rates(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} shipping rates were activated.')
    activate_rates.short_description = "✅ Activate selected rates"
    
    def deactivate_rates(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} shipping rates were deactivated.')
    deactivate_rates.short_description = "❌ Deactivate selected rates"

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = [
        'get_user_link', 'get_address_info', 'get_location', 
        'get_contact_info', 'get_address_status', 'created_at'
    ]
    list_filter = ['country', 'is_default', 'created_at']
    search_fields = ['user__username', 'full_name', 'city', 'country', 'phone_number']
    readonly_fields = ['created_at', 'updated_at', 'get_address_summary']
    ordering = ['-created_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name')
        }),
        ('Address Details', {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Contact & Preferences', {
            'fields': ('phone_number', 'is_default')
        }),
        ('Address Summary', {
            'fields': ('get_address_summary', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_user_link(self, obj):
        """Display user with link"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a>',
            user_url, obj.user.get_full_name() or obj.user.username
        )
    get_user_link.short_description = 'User'
    
    def get_address_info(self, obj):
        """Display address recipient info"""
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            obj.full_name,
            obj.address_line_1
        )
    get_address_info.short_description = 'Recipient & Address'
    
    def get_location(self, obj):
        """Display location information"""
        location_parts = []
        if obj.city:
            location_parts.append(obj.city)
        if obj.state:
            location_parts.append(obj.state)
        if obj.country:
            location_parts.append(obj.country)
            
        location = ', '.join(location_parts)
        
        # Add flag emoji for common countries
        country_flags = {
            'Tanzania': '🇹🇿',
            'Kenya': '🇰🇪',
            'Uganda': '🇺🇬',
            'Rwanda': '🇷🇼',
            'United States': '🇺🇸',
            'United Kingdom': '🇬🇧'
        }
        flag = country_flags.get(obj.country, '🌍')
        
        return format_html(
            '{} {}<br><small class="text-muted">📮 {}</small>',
            flag, location, obj.postal_code or 'No postal code'
        )
    get_location.short_description = 'Location'
    
    def get_contact_info(self, obj):
        """Display contact information"""
        if obj.phone_number:
            return format_html(
                '<span class="badge bg-info">📱 {}</span>',
                obj.phone_number
            )
        return format_html('<span class="text-muted">No phone</span>')
    get_contact_info.short_description = 'Contact'
    
    def get_address_status(self, obj):
        """Display address status"""
        badges = []
        
        if obj.is_default:
            badges.append('<span class="badge bg-primary">⭐ Default</span>')
        else:
            badges.append('<span class="badge bg-secondary">📍 Alternative</span>')
            
        return mark_safe('<br>'.join(badges))
    get_address_status.short_description = 'Status'
    
    def get_address_summary(self, obj):
        """Display comprehensive address summary"""
        if obj.pk:
            summary = f"""
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">📮 Complete Address</h6>
                </div>
                <div class="card-body">
                    <address>
                        <strong>{obj.full_name}</strong><br>
                        {obj.address_line_1}<br>
                        {obj.address_line_2 + '<br>' if obj.address_line_2 else ''}
                        {obj.city}, {obj.state or ''} {obj.postal_code or ''}<br>
                        {obj.country}<br>
                        {'📱 ' + obj.phone_number if obj.phone_number else ''}
                    </address>
                    <p><strong>Default Address:</strong> {'Yes' if obj.is_default else 'No'}</p>
                    <p><strong>Created:</strong> {obj.created_at.strftime('%B %d, %Y')}</p>
                </div>
            </div>
            """
            return mark_safe(summary)
        return '-'
    get_address_summary.short_description = 'Address Summary'
    
    actions = ['set_as_default', 'unset_as_default']
    
    def set_as_default(self, request, queryset):
        for address in queryset:
            # First unset all other defaults for this user
            ShippingAddress.objects.filter(user=address.user).update(is_default=False)
            # Then set this one as default
            address.is_default = True
            address.save()
        self.message_user(request, f'{queryset.count()} addresses were set as default for their respective users.')
    set_as_default.short_description = "⭐ Set as default address"
    
    def unset_as_default(self, request, queryset):
        updated = queryset.update(is_default=False)
        self.message_user(request, f'{updated} addresses were unset as default.')
    unset_as_default.short_description = "📍 Unset as default"

@admin.register(Tracking)
class TrackingAdmin(admin.ModelAdmin):
    list_display = [
        'get_order_link', 'get_tracking_info', 'get_carrier_badge', 
        'get_status_badge', 'get_delivery_info', 'updated_at'
    ]
    list_filter = ['carrier', 'status', 'updated_at', 'delivered_at']
    search_fields = ['order__id', 'tracking_number', 'carrier', 'current_location']
    readonly_fields = ['created_at', 'updated_at', 'get_tracking_timeline']
    ordering = ['-updated_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order', 'tracking_number', 'carrier')
        }),
        ('Current Status', {
            'fields': ('status', 'current_location', 'notes')
        }),
        ('Delivery Information', {
            'fields': ('estimated_delivery', 'delivered_at')
        }),
        ('Tracking Timeline', {
            'fields': ('get_tracking_timeline', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_order_link(self, obj):
        """Display order with link"""
        order_url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">Order #{:05d}</a>',
            order_url, obj.order.id
        )
    get_order_link.short_description = 'Order'
    
    def get_tracking_info(self, obj):
        """Display tracking information"""
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            obj.tracking_number,
            obj.current_location or 'Location not updated'
        )
    get_tracking_info.short_description = 'Tracking Details'
    
    def get_carrier_badge(self, obj):
        """Display carrier with badge"""
        carrier_colors = {
            'DHL': 'warning',
            'FedEx': 'primary',
            'UPS': 'success',
            'USPS': 'info'
        }
        color = carrier_colors.get(obj.carrier, 'dark')
        
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.carrier
        )
    get_carrier_badge.short_description = 'Carrier'
    
    def get_status_badge(self, obj):
        """Display status with appropriate styling"""
        status_configs = {
            'pending': ('secondary', '⏳'),
            'picked_up': ('info', '📦'),
            'in_transit': ('primary', '🚛'),
            'out_for_delivery': ('warning', '🚚'),
            'delivered': ('success', '✅'),
            'failed': ('danger', '❌'),
            'returned': ('dark', '↩️')
        }
        
        color, icon = status_configs.get(obj.status, ('secondary', '❓'))
        
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color, icon, obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_delivery_info(self, obj):
        """Display delivery information"""
        if obj.delivered_at:
            return format_html(
                '<span class="text-success">✅ Delivered</span><br><small>{}</small>',
                obj.delivered_at.strftime('%B %d, %Y')
            )
        elif obj.estimated_delivery:
            from django.utils import timezone
            if obj.estimated_delivery < timezone.now().date():
                return format_html(
                    '<span class="text-danger">⚠️ Overdue</span><br><small>Est: {}</small>',
                    obj.estimated_delivery.strftime('%B %d, %Y')
                )
            else:
                return format_html(
                    '<span class="text-primary">📅 Est: {}</span>',
                    obj.estimated_delivery.strftime('%B %d, %Y')
                )
        return format_html('<span class="text-muted">Not estimated</span>')
    get_delivery_info.short_description = 'Delivery'
    
    def get_tracking_timeline(self, obj):
        """Display tracking timeline"""
        if obj.pk:
            timeline = f"""
            <div class="card">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0">📦 Tracking Timeline</h6>
                </div>
                <div class="card-body">
                    <div class="timeline">
                        <div class="timeline-item">
                            <strong>Order Created:</strong> {obj.order.created_at.strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                        <div class="timeline-item">
                            <strong>Tracking Started:</strong> {obj.created_at.strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                        <div class="timeline-item">
                            <strong>Current Status:</strong> {obj.get_status_display()}
                        </div>
                        <div class="timeline-item">
                            <strong>Last Update:</strong> {obj.updated_at.strftime('%B %d, %Y at %I:%M %p')}
                        </div>
                        {f'<div class="timeline-item text-success"><strong>Delivered:</strong> {obj.delivered_at.strftime("%B %d, %Y at %I:%M %p")}</div>' if obj.delivered_at else ''}
                    </div>
                    <hr>
                    <p><strong>Tracking Number:</strong> {obj.tracking_number}</p>
                    <p><strong>Carrier:</strong> {obj.carrier}</p>
                    <p><strong>Current Location:</strong> {obj.current_location or 'Not specified'}</p>
                    <p><strong>Notes:</strong> {obj.notes or 'No notes'}</p>
                </div>
            </div>
            """
            return mark_safe(timeline)
        return '-'
    get_tracking_timeline.short_description = 'Tracking Timeline'
    
    actions = ['mark_delivered', 'mark_in_transit', 'mark_failed']
    
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='delivered', delivered_at=timezone.now())
        self.message_user(request, f'{updated} packages were marked as delivered.')
    mark_delivered.short_description = "✅ Mark as delivered"
    
    def mark_in_transit(self, request, queryset):
        updated = queryset.update(status='in_transit')
        self.message_user(request, f'{updated} packages were marked as in transit.')
    mark_in_transit.short_description = "🚛 Mark as in transit"
    
    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} deliveries were marked as failed.')
    mark_failed.short_description = "❌ Mark as failed delivery"

# Import models for aggregate functions
from django.db import models
