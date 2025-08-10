from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import (
    Store, StoreCategory, StoreReview, StoreApplication, 
    StoreSubscription, StoreAnalytics, StoreNotification, StoreFollower
)


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'owner_link', 'status', 'store_type', 'product_count_display',
        'total_sales', 'rating', 'created_at', 'store_actions'
    ]
    list_filter = ['status', 'store_type', 'created_at', 'country']
    search_fields = ['name', 'owner__username', 'owner__email', 'email']
    readonly_fields = [
        'slug', 'total_sales', 'total_revenue', 'rating', 'review_count',
        'created_at', 'updated_at', 'logo_preview', 'banner_preview'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'slug', 'description', 'short_description', 'store_type', 'status')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Business Information', {
            'fields': ('business_license', 'tax_id', 'bank_account'),
            'classes': ('collapse',)
        }),
        ('Store Branding', {
            'fields': ('logo', 'logo_preview', 'banner', 'banner_preview'),
            'classes': ('collapse',)
        }),
        ('Policies', {
            'fields': ('return_policy', 'shipping_policy'),
            'classes': ('collapse',)
        }),
        ('Performance Metrics', {
            'fields': ('commission_rate', 'total_sales', 'total_revenue', 'rating', 'review_count'),
            'classes': ('collapse',)
        }),
        ('Social Media', {
            'fields': ('website', 'facebook', 'instagram', 'twitter'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        })
    )
    
    def owner_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.owner.id])
        return format_html('<a href="{}">{}</a>', url, obj.owner.username)
    owner_link.short_description = 'Owner'
    
    def product_count_display(self, obj):
        return obj.product_count
    product_count_display.short_description = 'Products'
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.logo.url)
        return "No logo"
    logo_preview.short_description = 'Logo Preview'
    
    def banner_preview(self, obj):
        if obj.banner:
            return format_html('<img src="{}" style="max-height: 100px;"/>', obj.banner.url)
        return "No banner"
    banner_preview.short_description = 'Banner Preview'
    
    def store_actions(self, obj):
        actions = []
        
        if obj.status == 'pending':
            actions.append('<span class="button">Pending Approval</span>')
        elif obj.status == 'active':
            actions.append('<span style="color: green;">✓ Active</span>')
        elif obj.status == 'suspended':
            actions.append('<span style="color: orange;">⚠ Suspended</span>')
        
        return mark_safe(' '.join(actions))
    store_actions.short_description = 'Actions'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner').annotate(
            product_count=Count('products')
        )


@admin.register(StoreApplication)
class StoreApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'store_name', 'user_link', 'business_type', 'status', 
        'submitted_at', 'reviewed_at', 'application_actions'
    ]
    list_filter = ['status', 'business_type', 'submitted_at']
    search_fields = ['store_name', 'user__username', 'contact_email']
    readonly_fields = ['submitted_at', 'reviewed_at', 'user']
    actions = ['approve_applications', 'reject_applications']
    
    fieldsets = (
        ('Application Information', {
            'fields': ('user', 'store_name', 'store_description', 'business_type')
        }),
        ('Business Details', {
            'fields': ('business_license', 'tax_id')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'business_address')
        }),
        ('Documents', {
            'fields': ('license_document', 'tax_document', 'identity_document'),
            'classes': ('collapse',)
        }),
        ('Review Information', {
            'fields': ('status', 'admin_notes', 'rejection_reason', 'reviewed_by'),
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'reviewed_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:application_id>/approve/', self.approve_application, name='stores_storeapplication_approve'),
            path('<int:application_id>/reject/', self.reject_application, name='stores_storeapplication_reject'),
        ]
        return custom_urls + urls
    
    def approve_application(self, request, application_id):
        application = get_object_or_404(StoreApplication, id=application_id)
        
        if application.status == 'pending':
            application.status = 'approved'
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            
            # Create the store
            self.create_store_from_application(application)
            
            messages.success(request, f'Application for "{application.store_name}" has been approved and store created.')
        else:
            messages.warning(request, 'Application has already been reviewed.')
        
        return HttpResponseRedirect('/admin/stores/storeapplication/')
    
    def reject_application(self, request, application_id):
        application = get_object_or_404(StoreApplication, id=application_id)
        
        if application.status == 'pending':
            rejection_reason = request.POST.get('rejection_reason', '')
            application.status = 'rejected'
            application.rejection_reason = rejection_reason
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            
            messages.success(request, f'Application for "{application.store_name}" has been rejected.')
        else:
            messages.warning(request, 'Application has already been reviewed.')
        
        return HttpResponseRedirect('/admin/stores/storeapplication/')
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Applicant'
    
    def application_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<a href="/admin/stores/storeapplication/{}/approve/" class="button approve-btn" '
                'onclick="return confirm(\'Are you sure you want to approve this application?\')">Approve</a> '
                '<a href="#" onclick="rejectApplication({})" class="button reject-btn">Reject</a>',
                obj.id, obj.id
            )
        elif obj.status == 'approved':
            return '<span style="color: green;">✓ Approved</span>'
        elif obj.status == 'rejected':
            return '<span style="color: red;">✗ Rejected</span>'
        return obj.status.title()
    application_actions.short_description = 'Actions'
    
    def approve_applications(self, request, queryset):
        """Bulk approve applications"""
        count = 0
        for application in queryset.filter(status='pending'):
            application.status = 'approved'
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save()
            
            # Create the store
            self.create_store_from_application(application)
            count += 1
        
        self.message_user(request, f'{count} applications approved successfully.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        """Bulk reject applications"""
        count = queryset.filter(status='pending').update(
            status='rejected',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Bulk rejection by admin'
        )
        self.message_user(request, f'{count} applications rejected.')
    reject_applications.short_description = "Reject selected applications"
    
    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
            
            # If approved, create the store
            if obj.status == 'approved':
                self.create_store_from_application(obj)
        
        super().save_model(request, obj, form, change)
    
    def create_store_from_application(self, application):
        """Create a store when application is approved"""
        if not hasattr(application.user, 'store'):
            Store.objects.create(
                owner=application.user,
                name=application.store_name,
                description=application.store_description,
                store_type=application.business_type,
                email=application.contact_email,
                phone=application.contact_phone,
                address=application.business_address,
                business_license=application.business_license,
                tax_id=application.tax_id,
                status='active',
                approved_at=timezone.now()
            )


@admin.register(StoreReview)
class StoreReviewAdmin(admin.ModelAdmin):
    list_display = ['store_link', 'user_link', 'rating', 'title', 'is_verified', 'created_at']
    list_filter = ['rating', 'is_verified', 'created_at']
    search_fields = ['store__name', 'user__username', 'title', 'review']
    readonly_fields = ['created_at', 'updated_at']
    
    def store_link(self, obj):
        url = reverse('admin:stores_store_change', args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Reviewer'


@admin.register(StoreSubscription)
class StoreSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'store_link', 'plan', 'billing_cycle', 'monthly_fee', 
        'is_active', 'started_at', 'expires_at'
    ]
    list_filter = ['plan', 'billing_cycle', 'is_active']
    search_fields = ['store__name']
    
    def store_link(self, obj):
        url = reverse('admin:stores_store_change', args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'


@admin.register(StoreCategory)
class StoreCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(StoreAnalytics)
class StoreAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'store_link', 'date', 'daily_sales', 'daily_revenue', 
        'daily_orders', 'page_views', 'conversion_rate'
    ]
    list_filter = ['date', 'store']
    search_fields = ['store__name']
    date_hierarchy = 'date'
    
    def store_link(self, obj):
        url = reverse('admin:stores_store_change', args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'


@admin.register(StoreNotification)
class StoreNotificationAdmin(admin.ModelAdmin):
    list_display = ['store_link', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['store__name', 'title', 'message']
    
    def store_link(self, obj):
        url = reverse('admin:stores_store_change', args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'


@admin.register(StoreFollower)
class StoreFollowerAdmin(admin.ModelAdmin):
    list_display = ['store_link', 'user_link', 'created_at']
    list_filter = ['created_at']
    search_fields = ['store__name', 'user__username']
    
    def store_link(self, obj):
        url = reverse('admin:stores_store_change', args=[obj.store.id])
        return format_html('<a href="{}">{}</a>', url, obj.store.name)
    store_link.short_description = 'Store'
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Follower'


# Customize admin site header
admin.site.site_header = "DoleseCommerce Multi-Vendor Administration"
admin.site.site_title = "Store Admin"
admin.site.index_title = "Multi-Vendor Store Management"
