from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import UserProfile

# Unregister the default User admin
admin.site.unregister(User)

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('avatar', 'phone', 'country', 'date_of_birth')
        }),
        ('Address & Contact', {
            'fields': ('address', 'website')
        }),
        ('Profile Settings', {
            'fields': ('bio', 'is_public', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'get_full_name', 'get_user_status', 'get_profile_info', 'date_joined', 'is_active')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'userprofile__is_verified', 'userprofile__country')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'userprofile__phone')
    ordering = ('-date_joined',)
    
    def get_user_status(self, obj):
        """Display user status with badges"""
        status_badges = []
        
        if obj.is_superuser:
            status_badges.append('<span class="badge bg-danger">SuperUser</span>')
        elif obj.is_staff:
            status_badges.append('<span class="badge bg-warning">Staff</span>')
        else:
            status_badges.append('<span class="badge bg-info">Customer</span>')
            
        if hasattr(obj, 'userprofile') and obj.userprofile.is_verified:
            status_badges.append('<span class="badge bg-success">✓ Verified</span>')
            
        if not obj.is_active:
            status_badges.append('<span class="badge bg-secondary">Inactive</span>')
            
        return mark_safe(' '.join(status_badges))
    get_user_status.short_description = 'Status'
    
    def get_profile_info(self, obj):
        """Display profile information"""
        if hasattr(obj, 'userprofile'):
            profile = obj.userprofile
            info = []
            
            if profile.phone:
                info.append(f'📱 {profile.phone}')
            if profile.country:
                info.append(f'🌍 {profile.country}')
            if profile.is_public:
                info.append('👁️ Public')
                
            return mark_safe('<br>'.join(info)) if info else '-'
        return mark_safe('<span class="text-muted">No profile</span>')
    get_profile_info.short_description = 'Profile Info'
    
    def get_full_name(self, obj):
        """Display full name or username"""
        full_name = obj.get_full_name()
        return full_name if full_name else obj.username
    get_full_name.short_description = 'Name'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'get_avatar', 'phone', 'country', 'get_verification_status', 'get_profile_stats', 'created_at')
    list_filter = ('is_verified', 'is_public', 'country', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'address', 'country')
    readonly_fields = ('created_at', 'updated_at', 'get_user_link')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('get_user_link', 'avatar')
        }),
        ('Contact Details', {
            'fields': ('phone', 'address', 'country', 'website')
        }),
        ('Personal Information', {
            'fields': ('date_of_birth', 'bio')
        }),
        ('Profile Settings', {
            'fields': ('is_public', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_username(self, obj):
        """Display username with link to user"""
        return format_html(
            '<a href="{}" class="text-decoration-none">{}</a>',
            reverse('admin:auth_user_change', args=[obj.user.pk]),
            obj.user.username
        )
    get_username.short_description = 'Username'
    
    def get_avatar(self, obj):
        """Display avatar thumbnail"""
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; border: 2px solid #dee2e6;">',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(45deg, #007bff, #6f42c1); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 14px;">{}</div>',
            obj.user.username[0].upper()
        )
    get_avatar.short_description = 'Avatar'
    
    def get_verification_status(self, obj):
        """Display verification status"""
        if obj.is_verified:
            return format_html('<span class="badge bg-success">✓ Verified</span>')
        return format_html('<span class="badge bg-warning">⏳ Pending</span>')
    get_verification_status.short_description = 'Verification'
    
    def get_profile_stats(self, obj):
        """Display profile statistics"""
        stats = []
        
        if obj.is_public:
            stats.append('<span class="badge bg-info">👁️ Public</span>')
        else:
            stats.append('<span class="badge bg-secondary">🔒 Private</span>')
            
        if obj.website:
            stats.append('<span class="badge bg-primary">🌐 Website</span>')
            
        if obj.bio:
            bio_length = len(obj.bio)
            if bio_length > 100:
                stats.append('<span class="badge bg-success">📝 Rich Bio</span>')
            elif bio_length > 0:
                stats.append('<span class="badge bg-light text-dark">📝 Bio</span>')
                
        return mark_safe(' '.join(stats)) if stats else '-'
    get_profile_stats.short_description = 'Profile Stats'
    
    def get_user_link(self, obj):
        """Display link to user admin"""
        return format_html(
            '<a href="{}" class="btn btn-outline-primary btn-sm">👤 View User Details</a>',
            reverse('admin:auth_user_change', args=[obj.user.pk])
        )
    get_user_link.short_description = 'User Account'
    
    actions = ['verify_users', 'unverify_users', 'make_public', 'make_private']
    
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users were successfully verified.')
    verify_users.short_description = "✓ Verify selected users"
    
    def unverify_users(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} users were unverified.')
    unverify_users.short_description = "✗ Unverify selected users"
    
    def make_public(self, request, queryset):
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} profiles were made public.')
    make_public.short_description = "👁️ Make profiles public"
    
    def make_private(self, request, queryset):
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} profiles were made private.')
    make_private.short_description = "🔒 Make profiles private"

# Customize admin site header
admin.site.site_header = "DoleseCommerce User Management"
admin.site.site_title = "DoleseCommerce Admin"
admin.site.index_title = "Welcome to DoleseCommerce Administration"
