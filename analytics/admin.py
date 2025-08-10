from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Sum, Avg, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    UserActivity, ProductAnalytics, SalesReport, SearchAnalytics,
    SearchQuery, UserInteraction, ConversionFunnel, ABTest, BusinessMetric
)

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = [
        'get_action_badge', 'get_user_link', 'get_product_link', 
        'get_activity_details', 'timestamp'
    ]
    list_filter = ['action', 'timestamp', 'user__is_staff']
    search_fields = ['user__username', 'product__name', 'search_query']
    readonly_fields = ['timestamp', 'get_activity_summary']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('action', 'user', 'product', 'search_query')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Activity Summary', {
            'fields': ('get_activity_summary', 'timestamp'),
            'classes': ('collapse',)
        }),
    )
    
    def get_action_badge(self, obj):
        """Display action with appropriate badge"""
        action_configs = {
            'view': ('info', '👁️'),
            'add_to_cart': ('primary', '🛒'),
            'purchase': ('success', '💰'),
            'search': ('warning', '🔍'),
            'login': ('secondary', '🔑'),
            'logout': ('dark', '🚪'),
            'register': ('success', '📝'),
            'wishlist': ('danger', '❤️')
        }
        
        color, icon = action_configs.get(obj.action, ('secondary', '📊'))
        
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color, icon, obj.get_action_display()
        )
    get_action_badge.short_description = 'Action'
    
    def get_user_link(self, obj):
        """Display user with link and info"""
        if obj.user:
            user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
            user_display = obj.user.get_full_name() or obj.user.username
            
            # Add user type badge
            if obj.user.is_superuser:
                badge = '<span class="badge bg-danger">Admin</span>'
            elif obj.user.is_staff:
                badge = '<span class="badge bg-warning">Staff</span>'
            else:
                badge = '<span class="badge bg-info">Customer</span>'
                
            return format_html(
                '<a href="{}" class="text-decoration-none">{}</a><br>{}',
                user_url, user_display, badge
            )
        return format_html('<span class="text-muted">Anonymous</span>')
    get_user_link.short_description = 'User'
    
    def get_product_link(self, obj):
        """Display product with link"""
        if obj.product:
            product_url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html(
                '<a href="{}" class="text-decoration-none">{}</a><br>'
                '<small class="text-muted">SKU: {}</small>',
                product_url, obj.product.name, obj.product.sku or 'N/A'
            )
        return '-'
    get_product_link.short_description = 'Product'
    
    def get_activity_details(self, obj):
        """Display activity details"""
        details = []
        
        if obj.search_query:
            details.append(f'🔍 "{obj.search_query}"')
        if obj.ip_address:
            details.append(f'🌐 {obj.ip_address}')
            
        return format_html('<br>'.join(details[:2])) if details else '-'
    get_activity_details.short_description = 'Details'
    
    def get_activity_summary(self, obj):
        """Display comprehensive activity summary"""
        if obj.pk:
            summary = f"""
            <div class="card">
                <div class="card-header bg-primary text-white">
                    <h6 class="mb-0">📊 Activity Summary</h6>
                </div>
                <div class="card-body">
                    <p><strong>Action:</strong> {obj.get_action_display()}</p>
                    <p><strong>User:</strong> {obj.user.get_full_name() or obj.user.username if obj.user else 'Anonymous'}</p>
                    <p><strong>Product:</strong> {obj.product.name if obj.product else 'N/A'}</p>
                    <p><strong>Search Query:</strong> {obj.search_query or 'N/A'}</p>
                    <p><strong>IP Address:</strong> {obj.ip_address or 'N/A'}</p>
                    <p><strong>User Agent:</strong> {(obj.user_agent[:50] + '...') if obj.user_agent and len(obj.user_agent) > 50 else obj.user_agent or 'N/A'}</p>
                    <p><strong>Timestamp:</strong> {obj.timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
            </div>
            """
            return mark_safe(summary)
        return '-'
    get_activity_summary.short_description = 'Activity Summary'

@admin.register(ProductAnalytics)
class ProductAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'get_product_link', 'get_views_display', 'get_conversion_rate', 
        'get_performance_indicators', 'last_updated'
    ]
    list_filter = ['last_updated', 'product__category']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['last_updated', 'get_analytics_dashboard']
    ordering = ['-total_views']
    
    fieldsets = (
        ('Product Information', {
            'fields': ('product',)
        }),
        ('Analytics Data', {
            'fields': ('total_views', 'conversion_rate', 'last_updated')
        }),
        ('Analytics Dashboard', {
            'fields': ('get_analytics_dashboard',),
            'classes': ('collapse',)
        }),
    )
    
    def get_product_link(self, obj):
        """Display product with link and image"""
        product_url = reverse('admin:products_product_change', args=[obj.product.pk])
        
        # Try to get product image
        image_html = ""
        if hasattr(obj.product, 'images') and obj.product.images.exists():
            image = obj.product.images.first()
            image_html = f'<img src="{image.image.url}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 8px; margin-right: 8px;">'
        
        return format_html(
            '{}<a href="{}" class="text-decoration-none">{}</a><br>'
            '<small class="text-muted">SKU: {} | Category: {}</small>',
            image_html, product_url, obj.product.name,
            obj.product.sku or 'N/A',
            obj.product.category.name if obj.product.category else 'N/A'
        )
    get_product_link.short_description = 'Product'
    
    def get_views_display(self, obj):
        """Display total views with trend indicator"""
        # Calculate views trend (this would need historical data)
        return format_html(
            '<strong class="text-primary">{:,}</strong><br>'
            '<small class="text-muted">views</small>',
            obj.total_views
        )
    get_views_display.short_description = 'Total Views'
    
    def get_conversion_rate(self, obj):
        """Display conversion rate with color coding"""
        rate = obj.conversion_rate or 0
        
        if rate >= 5:
            color = 'success'
            indicator = '🔥'
        elif rate >= 2:
            color = 'primary'
            indicator = '📈'
        elif rate >= 1:
            color = 'warning'
            indicator = '⚡'
        else:
            color = 'danger'
            indicator = '📉'
            
        return format_html(
            '<span class="badge bg-{} fs-6">{} {:.2f}%</span>',
            color, indicator, rate
        )
    get_conversion_rate.short_description = 'Conversion Rate'
    
    def get_performance_indicators(self, obj):
        """Display performance indicators"""
        indicators = []
        
        # High views indicator
        if obj.total_views > 1000:
            indicators.append('<span class="badge bg-info">🔥 Popular</span>')
        elif obj.total_views > 100:
            indicators.append('<span class="badge bg-secondary">👁️ Viewed</span>')
            
        # Conversion rate indicator
        if obj.conversion_rate and obj.conversion_rate > 3:
            indicators.append('<span class="badge bg-success">💰 High Converting</span>')
            
        return mark_safe('<br>'.join(indicators)) if indicators else '-'
    get_performance_indicators.short_description = 'Performance'
    
    def get_analytics_dashboard(self, obj):
        """Display analytics dashboard"""
        if obj.pk:
            # Calculate additional metrics
            avg_conversion = ProductAnalytics.objects.aggregate(avg_rate=Avg('conversion_rate'))['avg_rate'] or 0
            total_products = ProductAnalytics.objects.count()
            
            dashboard = f"""
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0">📈 Performance Metrics</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Total Views:</strong> {obj.total_views:,}</p>
                            <p><strong>Conversion Rate:</strong> {obj.conversion_rate:.2f}%</p>
                            <p><strong>vs. Average:</strong> {obj.conversion_rate - avg_conversion:.2f}% {'above' if obj.conversion_rate > avg_conversion else 'below'} average</p>
                            <p><strong>Last Updated:</strong> {obj.last_updated.strftime('%B %d, %Y')}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-success text-white">
                            <h6 class="mb-0">🎯 Product Context</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Product Name:</strong> {obj.product.name}</p>
                            <p><strong>Category:</strong> {obj.product.category.name if obj.product.category else 'N/A'}</p>
                            <p><strong>Price:</strong> TZS {obj.product.price:,.2f}</p>
                            <p><strong>Stock:</strong> {getattr(obj.product, 'stock_quantity', 'N/A')}</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return mark_safe(dashboard)
        return '-'
    get_analytics_dashboard.short_description = 'Analytics Dashboard'

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'get_sales_display', 'get_orders_display', 
        'get_aov_display', 'get_performance_indicators'
    ]
    list_filter = ['date']
    ordering = ['-date']
    readonly_fields = ['get_sales_summary']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Report Date', {
            'fields': ('date',)
        }),
        ('Sales Metrics', {
            'fields': ('total_sales', 'total_orders', 'average_order_value')
        }),
        ('Sales Summary', {
            'fields': ('get_sales_summary',),
            'classes': ('collapse',)
        }),
    )
    
    def get_sales_display(self, obj):
        """Display total sales with formatting"""
        return format_html(
            '<strong class="text-success">TZS {:,.2f}</strong>',
            obj.total_sales
        )
    get_sales_display.short_description = 'Total Sales'
    
    def get_orders_display(self, obj):
        """Display total orders"""
        return format_html(
            '<span class="badge bg-primary">{} orders</span>',
            obj.total_orders
        )
    get_orders_display.short_description = 'Orders'
    
    def get_aov_display(self, obj):
        """Display average order value"""
        return format_html(
            '<span class="badge bg-info">TZS {:,.2f}</span>',
            obj.average_order_value
        )
    get_aov_display.short_description = 'Avg Order Value'
    
    def get_performance_indicators(self, obj):
        """Display performance indicators"""
        indicators = []
        
        # Compare with previous day if available
        previous_day = SalesReport.objects.filter(
            date=obj.date - timedelta(days=1)
        ).first()
        
        if previous_day:
            sales_change = ((obj.total_sales - previous_day.total_sales) / previous_day.total_sales * 100) if previous_day.total_sales > 0 else 0
            
            if sales_change > 10:
                indicators.append('<span class="badge bg-success">📈 Strong Growth</span>')
            elif sales_change > 0:
                indicators.append('<span class="badge bg-info">📊 Growth</span>')
            elif sales_change < -10:
                indicators.append('<span class="badge bg-danger">📉 Decline</span>')
                
        # High sales day indicator
        if obj.total_sales > 100000:  # 100K TZS
            indicators.append('<span class="badge bg-warning">🔥 High Sales Day</span>')
            
        return mark_safe('<br>'.join(indicators)) if indicators else '-'
    get_performance_indicators.short_description = 'Performance'
    
    def get_sales_summary(self, obj):
        """Display sales summary"""
        if obj.pk:
            # Calculate weekly and monthly totals
            week_start = obj.date - timedelta(days=obj.date.weekday())
            month_start = obj.date.replace(day=1)
            
            weekly_sales = SalesReport.objects.filter(
                date__gte=week_start, date__lte=obj.date
            ).aggregate(total=Sum('total_sales'))['total'] or 0
            
            monthly_sales = SalesReport.objects.filter(
                date__gte=month_start, date__lte=obj.date
            ).aggregate(total=Sum('total_sales'))['total'] or 0
            
            summary = f"""
            <div class="card">
                <div class="card-header bg-success text-white">
                    <h6 class="mb-0">💰 Sales Summary for {obj.date.strftime('%B %d, %Y')}</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <h6>Daily Performance</h6>
                            <p><strong>Sales:</strong> TZS {obj.total_sales:,.2f}</p>
                            <p><strong>Orders:</strong> {obj.total_orders}</p>
                            <p><strong>AOV:</strong> TZS {obj.average_order_value:,.2f}</p>
                        </div>
                        <div class="col-md-4">
                            <h6>Weekly Context</h6>
                            <p><strong>Week Total:</strong> TZS {weekly_sales:,.2f}</p>
                            <p><strong>Daily Average:</strong> TZS {weekly_sales/7:,.2f}</p>
                        </div>
                        <div class="col-md-4">
                            <h6>Monthly Context</h6>
                            <p><strong>Month Total:</strong> TZS {monthly_sales:,.2f}</p>
                            <p><strong>Daily Average:</strong> TZS {monthly_sales/obj.date.day:,.2f}</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return mark_safe(summary)
        return '-'
    get_sales_summary.short_description = 'Sales Summary'

@admin.register(SearchAnalytics)
class SearchAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'get_query_display', 'get_search_count', 'get_results_count', 
        'get_ctr_display', 'get_search_performance'
    ]
    search_fields = ['query']
    ordering = ['-search_count']
    readonly_fields = ['get_search_insights']
    
    fieldsets = (
        ('Search Query', {
            'fields': ('query',)
        }),
        ('Search Metrics', {
            'fields': ('search_count', 'results_count', 'click_through_rate')
        }),
        ('Search Insights', {
            'fields': ('get_search_insights',),
            'classes': ('collapse',)
        }),
    )
    
    def get_query_display(self, obj):
        """Display search query with formatting"""
        return format_html(
            '<strong>"{}"</strong><br><small class="text-muted">{} characters</small>',
            obj.query, len(obj.query)
        )
    get_query_display.short_description = 'Search Query'
    
    def get_search_count(self, obj):
        """Display search count with badge"""
        if obj.search_count > 100:
            color = 'success'
            icon = '🔥'
        elif obj.search_count > 50:
            color = 'primary'
            icon = '📈'
        else:
            color = 'secondary'
            icon = '🔍'
            
        return format_html(
            '<span class="badge bg-{}">{} {} searches</span>',
            color, icon, obj.search_count
        )
    get_search_count.short_description = 'Search Count'
    
    def get_results_count(self, obj):
        """Display results count"""
        if obj.results_count == 0:
            return format_html('<span class="badge bg-danger">❌ No Results</span>')
        elif obj.results_count < 5:
            return format_html('<span class="badge bg-warning">⚠️ {} results</span>', obj.results_count)
        else:
            return format_html('<span class="badge bg-success">✅ {} results</span>', obj.results_count)
    get_results_count.short_description = 'Results'
    
    def get_ctr_display(self, obj):
        """Display click-through rate"""
        rate = obj.click_through_rate or 0
        
        if rate >= 20:
            color = 'success'
            indicator = '🎯'
        elif rate >= 10:
            color = 'primary'
            indicator = '👆'
        elif rate >= 5:
            color = 'warning'
            indicator = '📊'
        else:
            color = 'danger'
            indicator = '📉'
            
        return format_html(
            '<span class="badge bg-{}">{} {:.1f}%</span>',
            color, indicator, rate
        )
    get_ctr_display.short_description = 'Click-Through Rate'
    
    def get_search_performance(self, obj):
        """Display search performance indicators"""
        indicators = []
        
        # Popular search
        if obj.search_count > 50:
            indicators.append('<span class="badge bg-info">🔥 Popular</span>')
            
        # Zero results
        if obj.results_count == 0:
            indicators.append('<span class="badge bg-danger">❌ Zero Results</span>')
            
        # High CTR
        if obj.click_through_rate and obj.click_through_rate > 15:
            indicators.append('<span class="badge bg-success">🎯 High CTR</span>')
            
        # Low CTR
        if obj.click_through_rate and obj.click_through_rate < 5:
            indicators.append('<span class="badge bg-warning">📉 Low CTR</span>')
            
        return mark_safe('<br>'.join(indicators)) if indicators else '-'
    get_search_performance.short_description = 'Performance'
    
    def get_search_insights(self, obj):
        """Display search insights"""
        if obj.pk:
            # Calculate some insights
            avg_ctr = SearchAnalytics.objects.aggregate(avg_ctr=Avg('click_through_rate'))['avg_ctr'] or 0
            total_searches = SearchAnalytics.objects.aggregate(total=Sum('search_count'))['total'] or 0
            search_percentage = (obj.search_count / total_searches * 100) if total_searches > 0 else 0
            
            insights = f"""
            <div class="card">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">🔍 Search Insights for "{obj.query}"</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Search Performance</h6>
                            <p><strong>Search Count:</strong> {obj.search_count:,}</p>
                            <p><strong>Results Found:</strong> {obj.results_count:,}</p>
                            <p><strong>Click-Through Rate:</strong> {obj.click_through_rate:.2f}%</p>
                            <p><strong>vs. Average CTR:</strong> {obj.click_through_rate - avg_ctr:.2f}% {'above' if obj.click_through_rate > avg_ctr else 'below'} average</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Search Context</h6>
                            <p><strong>Query Length:</strong> {len(obj.query)} characters</p>
                            <p><strong>Word Count:</strong> {len(obj.query.split())} words</p>
                            <p><strong>Search Share:</strong> {search_percentage:.2f}% of all searches</p>
                            <p><strong>Status:</strong> {'Popular Query' if obj.search_count > 50 else 'Regular Query'}</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return mark_safe(insights)
        return '-'
    get_search_insights.short_description = 'Search Insights'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'results_count', 'created_at']
    list_filter = ['created_at', 'results_count']
    search_fields = ['query', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Query Information', {
            'fields': ('query', 'user', 'results_count')
        }),
        ('Technical Details', {
            'fields': ('filters', 'ip_address', 'created_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'interaction_type', 'timestamp']
    list_filter = ['interaction_type', 'timestamp']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Interaction Details', {
            'fields': ('user', 'product', 'interaction_type', 'timestamp')
        }),
        ('Session Information', {
            'fields': ('session_id', 'ip_address', 'user_agent', 'referrer'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ConversionFunnel)
class ConversionFunnelAdmin(admin.ModelAdmin):
    list_display = ['user', 'stage', 'product', 'timestamp']
    list_filter = ['stage', 'timestamp']
    search_fields = ['user__username', 'product__name', 'session_id']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Funnel Stage', {
            'fields': ('user', 'session_id', 'stage', 'product', 'timestamp')
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ABTest)
class ABTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'start_date', 'end_date', 'traffic_allocation']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Test Configuration', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Test Parameters', {
            'fields': ('start_date', 'end_date', 'traffic_allocation')
        }),
        ('System Information', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BusinessMetric)
class BusinessMetricAdmin(admin.ModelAdmin):
    list_display = ['metric_type', 'value', 'date', 'created_at']
    list_filter = ['metric_type', 'date']
    search_fields = ['metric_type']
    readonly_fields = ['created_at']
    ordering = ['-date', 'metric_type']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Metric Information', {
            'fields': ('metric_type', 'value', 'date')
        }),
        ('Additional Data', {
            'fields': ('metadata', 'created_at'),
            'classes': ('collapse',)
        }),
    )


# Custom admin site configuration
admin.site.site_header = "E-Commerce Analytics Administration"
admin.site.site_title = "Analytics Admin"
admin.site.index_title = "Analytics Management Dashboard"
