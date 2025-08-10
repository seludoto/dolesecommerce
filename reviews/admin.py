from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Avg, Count
from .models import Review, ReviewHelpfulness, ReviewImage, ReviewReport

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 0
    readonly_fields = ('uploaded_at', 'get_image_preview')
    fields = ('image', 'get_image_preview', 'caption', 'uploaded_at')
    
    def get_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; border: 2px solid #dee2e6;">',
                obj.image.url
            )
        return '-'
    get_image_preview.short_description = 'Preview'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'get_review_summary', 'get_product_link', 'get_user_info', 
        'get_rating_display', 'get_status_badges', 'get_helpfulness', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at', 'product__category']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at', 'helpful_count', 'get_review_stats']
    ordering = ['-created_at']
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('Review Content', {
            'fields': ('product', 'user', 'rating', 'title', 'comment')
        }),
        ('Review Status', {
            'fields': ('is_approved', 'is_verified_purchase')
        }),
        ('Statistics & Analytics', {
            'fields': ('get_review_stats', 'helpful_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_review_summary(self, obj):
        """Display review title with truncated preview"""
        title = obj.title or "Untitled Review"
        comment_preview = (obj.comment[:50] + '...') if len(obj.comment) > 50 else obj.comment
        
        return format_html(
            '<strong>{}</strong><br><small class="text-muted">{}</small>',
            title, comment_preview
        )
    get_review_summary.short_description = 'Review'
    
    def get_product_link(self, obj):
        """Display product with link and image"""
        product_url = reverse('admin:products_product_change', args=[obj.product.pk])
        
        # Try to get product image
        image_html = ""
        if hasattr(obj.product, 'images') and obj.product.images.exists():
            image = obj.product.images.first()
            image_html = f'<img src="{image.image.url}" style="width: 30px; height: 30px; object-fit: cover; border-radius: 4px; margin-right: 8px;">'
        
        return format_html(
            '{}<a href="{}" class="text-decoration-none">{}</a>',
            image_html, product_url, obj.product.name
        )
    get_product_link.short_description = 'Product'
    
    def get_user_info(self, obj):
        """Display user information with profile link"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        full_name = obj.user.get_full_name() or obj.user.username
        
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br><small class="text-muted">{}</small>',
            user_url, full_name, obj.user.username
        )
    get_user_info.short_description = 'Reviewer'
    
    def get_rating_display(self, obj):
        """Display rating with stars"""
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = 'text-warning'
        
        return format_html(
            '<span class="{}" style="font-size: 16px;">{}</span><br><small>{}/5</small>',
            color, stars, obj.rating
        )
    get_rating_display.short_description = 'Rating'
    
    def get_status_badges(self, obj):
        """Display status badges"""
        badges = []
        
        if obj.is_approved:
            badges.append('<span class="badge bg-success">✓ Approved</span>')
        else:
            badges.append('<span class="badge bg-warning">⏳ Pending</span>')
            
        if obj.is_verified_purchase:
            badges.append('<span class="badge bg-primary">🛒 Verified Purchase</span>')
            
        # Check if review has images
        if obj.images.exists():
            badges.append('<span class="badge bg-info">📸 Has Images</span>')
            
        return mark_safe('<br>'.join(badges))
    get_status_badges.short_description = 'Status'
    
    def get_helpfulness(self, obj):
        """Display helpfulness statistics"""
        helpful_count = obj.helpfulness.filter(is_helpful=True).count()
        not_helpful_count = obj.helpfulness.filter(is_helpful=False).count()
        total_votes = helpful_count + not_helpful_count
        
        if total_votes == 0:
            return format_html('<small class="text-muted">No votes yet</small>')
            
        helpful_percentage = (helpful_count / total_votes) * 100
        
        color = 'success' if helpful_percentage >= 70 else 'warning' if helpful_percentage >= 50 else 'danger'
        
        return format_html(
            '<div class="text-center">'
            '<span class="badge bg-{}">{:.0f}% helpful</span><br>'
            '<small>{} of {} found helpful</small>'
            '</div>',
            color, helpful_percentage, helpful_count, total_votes
        )
    get_helpfulness.short_description = 'Helpfulness'
    
    def get_review_stats(self, obj):
        """Display comprehensive review statistics"""
        if obj.pk:
            stats = f"""
            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h6 class="mb-0">📊 Review Statistics</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Images:</strong> {obj.images.count()}</p>
                            <p><strong>Helpfulness Votes:</strong> {obj.helpfulness.count()}</p>
                            <p><strong>Reports:</strong> {obj.reports.count()}</p>
                            <p><strong>Word Count:</strong> {len(obj.comment.split()) if obj.comment else 0}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header bg-info text-white">
                            <h6 class="mb-0">🎯 Review Context</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Product Category:</strong> {obj.product.category.name if obj.product.category else 'N/A'}</p>
                            <p><strong>Product Rating:</strong> {obj.product.average_rating():.1f}/5 (from {obj.product.reviews.count()} reviews)</p>
                            <p><strong>Reviewer's Reviews:</strong> {obj.user.reviews.count()}</p>
                            <p><strong>Review Age:</strong> {(timezone.now() - obj.created_at).days} days</p>
                        </div>
                    </div>
                </div>
            </div>
            """
            return mark_safe(stats)
        return '-'
    get_review_stats.short_description = 'Detailed Statistics'
    
    actions = ['approve_reviews', 'disapprove_reviews', 'mark_verified_purchase']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'{updated} reviews were approved.')
    approve_reviews.short_description = "✓ Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} reviews were disapproved.')
    disapprove_reviews.short_description = "✗ Disapprove selected reviews"
    
    def mark_verified_purchase(self, request, queryset):
        updated = queryset.update(is_verified_purchase=True)
        self.message_user(request, f'{updated} reviews were marked as verified purchases.')
    mark_verified_purchase.short_description = "🛒 Mark as verified purchases"

@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    list_display = ['get_review_info', 'get_user_link', 'get_helpfulness_display', 'created_at']
    list_filter = ['is_helpful', 'created_at', 'review__rating']
    search_fields = ['review__product__name', 'user__username', 'review__title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_review_info(self, obj):
        """Display review information"""
        review_url = reverse('admin:reviews_review_change', args=[obj.review.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br>'
            '<small class="text-muted">Rating: {}★ | Product: {}</small>',
            review_url, 
            obj.review.title or "Untitled Review",
            obj.review.rating,
            obj.review.product.name
        )
    get_review_info.short_description = 'Review'
    
    def get_user_link(self, obj):
        """Display user with link"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a>',
            user_url, obj.user.get_full_name() or obj.user.username
        )
    get_user_link.short_description = 'User'
    
    def get_helpfulness_display(self, obj):
        """Display helpfulness with emoji"""
        if obj.is_helpful:
            return format_html('<span class="badge bg-success">👍 Helpful</span>')
        else:
            return format_html('<span class="badge bg-danger">👎 Not Helpful</span>')
    get_helpfulness_display.short_description = 'Vote'

@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['get_review_link', 'get_image_preview', 'caption', 'uploaded_at']
    list_filter = ['uploaded_at', 'review__rating']
    search_fields = ['review__product__name', 'caption', 'review__user__username']
    readonly_fields = ['uploaded_at', 'get_image_preview']
    ordering = ['-uploaded_at']
    
    def get_review_link(self, obj):
        """Display review link with info"""
        review_url = reverse('admin:reviews_review_change', args=[obj.review.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br>'
            '<small class="text-muted">{}★ | {}</small>',
            review_url,
            obj.review.title or "Untitled Review",
            obj.review.rating,
            obj.review.product.name
        )
    get_review_link.short_description = 'Review'
    
    def get_image_preview(self, obj):
        """Display image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px; border: 2px solid #dee2e6; cursor: pointer;" '
                'onclick="window.open(\'{}\', \'_blank\')" title="Click to view full size">',
                obj.image.url, obj.image.url
            )
        return '-'
    get_image_preview.short_description = 'Image Preview'

@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = [
        'get_review_info', 'get_reporter_link', 'get_reason_display', 
        'get_status_badge', 'created_at', 'get_report_actions'
    ]
    list_filter = ['reason', 'is_resolved', 'created_at', 'review__rating']
    search_fields = ['review__product__name', 'reporter__username', 'comment', 'review__title']
    readonly_fields = ['created_at', 'get_report_summary']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('review', 'reporter', 'reason', 'comment')
        }),
        ('Report Status', {
            'fields': ('is_resolved',)
        }),
        ('Report Summary', {
            'fields': ('get_report_summary', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_review_info(self, obj):
        """Display review information"""
        review_url = reverse('admin:reviews_review_change', args=[obj.review.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a><br>'
            '<small class="text-muted">{}★ | {}</small>',
            review_url,
            obj.review.title or "Untitled Review",
            obj.review.rating,
            obj.review.product.name
        )
    get_review_info.short_description = 'Reported Review'
    
    def get_reporter_link(self, obj):
        """Display reporter with link"""
        user_url = reverse('admin:auth_user_change', args=[obj.reporter.pk])
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a>',
            user_url, obj.reporter.get_full_name() or obj.reporter.username
        )
    get_reporter_link.short_description = 'Reporter'
    
    def get_reason_display(self, obj):
        """Display reason with appropriate styling"""
        reason_colors = {
            'spam': 'warning',
            'inappropriate': 'danger',
            'fake': 'danger',
            'other': 'secondary'
        }
        color = reason_colors.get(obj.reason, 'secondary')
        
        reason_icons = {
            'spam': '🔄',
            'inappropriate': '⚠️',
            'fake': '🚫',
            'other': '❓'
        }
        icon = reason_icons.get(obj.reason, '❓')
        
        return format_html(
            '<span class="badge bg-{}">{} {}</span>',
            color, icon, obj.get_reason_display()
        )
    get_reason_display.short_description = 'Reason'
    
    def get_status_badge(self, obj):
        """Display resolution status"""
        if obj.is_resolved:
            return format_html('<span class="badge bg-success">✅ Resolved</span>')
        else:
            return format_html('<span class="badge bg-warning">⏳ Pending</span>')
    get_status_badge.short_description = 'Status'
    
    def get_report_actions(self, obj):
        """Display quick action buttons"""
        if not obj.is_resolved:
            return format_html(
                '<button class="btn btn-sm btn-outline-success" onclick="location.href=\'?id={}&action=resolve\'">✓ Resolve</button>',
                obj.pk
            )
        return format_html('<span class="text-muted">Resolved</span>')
    get_report_actions.short_description = 'Actions'
    
    def get_report_summary(self, obj):
        """Display report summary"""
        if obj.pk:
            summary = f"""
            <div class="card">
                <div class="card-header bg-warning text-dark">
                    <h6 class="mb-0">🚨 Report Details</h6>
                </div>
                <div class="card-body">
                    <p><strong>Reporter:</strong> {obj.reporter.get_full_name() or obj.reporter.username}</p>
                    <p><strong>Reason:</strong> {obj.get_reason_display()}</p>
                    <p><strong>Comment:</strong> {obj.comment or 'No additional comment'}</p>
                    <p><strong>Review Rating:</strong> {obj.review.rating}★</p>
                    <p><strong>Review Author:</strong> {obj.review.user.get_full_name() or obj.review.user.username}</p>
                    <p><strong>Product:</strong> {obj.review.product.name}</p>
                    <p><strong>Status:</strong> {'Resolved' if obj.is_resolved else 'Pending'}</p>
                </div>
            </div>
            """
            return mark_safe(summary)
        return '-'
    get_report_summary.short_description = 'Report Summary'
    
    actions = ['mark_resolved', 'mark_unresolved']
    
    def mark_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f'{updated} reports were marked as resolved.')
    mark_resolved.short_description = "✅ Mark selected reports as resolved"
    
    def mark_unresolved(self, request, queryset):
        updated = queryset.update(is_resolved=False)
        self.message_user(request, f'{updated} reports were marked as unresolved.')
    mark_unresolved.short_description = "⏳ Mark selected reports as unresolved"

# Import timezone for date calculations
from django.utils import timezone
