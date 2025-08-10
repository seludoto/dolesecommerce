
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .forms import PhoneEmailAuthenticationForm, CustomUserCreationForm
from .models import UserProfile


@login_required
def profile_edit_view(request):
    user = request.user
    # Get or create UserProfile for the user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.username = request.POST.get('username', user.username)
        user.save()
        
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        profile.country = request.POST.get('country', profile.country)
        profile.bio = request.POST.get('bio', profile.bio)
        profile.website = request.POST.get('website', profile.website)
        
        if request.FILES.get('avatar'):
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('users:profile')
    
    return render(request, 'users/profile_edit.html', {'user': user, 'profile': profile})


@login_required
def profile_view(request):
    # Get or create UserProfile for the user
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if created:
        messages.info(request, 'Welcome! Your profile has been created.')
    
    return render(request, 'users/profile.html', {'profile': profile})


@login_required
def update_profile(request):
    """Update user profile from registry page"""
    if request.method == 'POST':
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Update profile fields
        bio = request.POST.get('bio', '')
        if hasattr(profile, 'bio'):
            profile.bio = bio
        profile.save()
        
        # Handle public profile setting
        public_profile = request.POST.get('public_profile') == 'on'
        if hasattr(profile, 'is_public'):
            profile.is_public = public_profile
            profile.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('core:registry')
    
    return redirect('core:registry')


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile for the new user
            UserProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome!')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = PhoneEmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Ensure UserProfile exists for the user
            UserProfile.objects.get_or_create(user=user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('users:dashboard')
        else:
            messages.error(request, 'Invalid login credentials.')
    else:
        form = PhoneEmailAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('users:login')


@login_required
def dashboard_view(request):
    """Enhanced user dashboard similar to 'My KiKUU'"""
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user statistics
    try:
        from orders.models import Order
        total_orders = Order.objects.filter(user=user).count()
        recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:3]
    except:
        total_orders = 0
        recent_orders = []
    
    try:
        from cart.models import Cart
        cart = Cart.objects.filter(user=user).first()
        cart_items = cart.total_items if cart else 0
    except:
        cart_items = 0
    
    try:
        from reviews.models import Review
        reviews_count = Review.objects.filter(user=user).count()
    except:
        reviews_count = 0
    
    try:
        from products.models import RecentlyViewed
        recently_viewed = RecentlyViewed.objects.filter(user=user).order_by('-viewed_at')[:4]
    except:
        recently_viewed = []
    
    # Get wishlist count and notifications
    try:
        from promotions.models import Wishlist, UserNotification
        wishlist, created = Wishlist.objects.get_or_create(user=user)
        wishlist_count = wishlist.total_items
        unread_notifications = UserNotification.objects.filter(user=user, is_read=False).count()
    except:
        wishlist_count = 0
        unread_notifications = 0
    
    context = {
        'profile': profile,
        'total_orders': total_orders,
        'wishlist_count': wishlist_count,
        'cart_items': cart_items,
        'reviews_count': reviews_count,
        'recent_orders': recent_orders,
        'recently_viewed': recently_viewed,
        'unread_notifications': unread_notifications,
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def wishlist_view(request):
    """User wishlist view using promotions.Wishlist model"""
    try:
        from promotions.models import Wishlist, WishlistItem
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        wishlist_items = wishlist.items.select_related('product').order_by('-added_at')
        wishlist_count = wishlist_items.count()
    except:
        wishlist_items = []
        wishlist_count = 0
    
    return render(request, 'users/wishlist.html', {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_count
    })


@login_required
def saved_for_later_view(request):
    """Saved for later items view"""
    try:
        from cart.models import SavedForLater
        saved_items = SavedForLater.objects.filter(user=request.user).order_by('-saved_at')
    except:
        saved_items = []
    
    return render(request, 'users/saved_for_later.html', {
        'saved_items': saved_items
    })


@login_required
def coupons_view(request):
    """User coupons and promo codes view"""
    try:
        from cart.models import PromoCode, CartPromoCode
        # Get available promo codes for the user
        available_coupons = PromoCode.objects.filter(
            is_active=True,
            valid_until__gte=timezone.now()
        ).order_by('-created_at')[:10]
        
        # Get used promo codes
        used_coupons = CartPromoCode.objects.filter(
            cart__user=request.user
        ).select_related('promo_code').order_by('-applied_at')[:5]
    except:
        available_coupons = []
        used_coupons = []
    
    return render(request, 'users/coupons.html', {
        'available_coupons': available_coupons,
        'used_coupons': used_coupons
    })


@login_required
def addresses_view(request):
    """Address book management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.address = request.POST.get('address', profile.address)
        profile.country = request.POST.get('country', profile.country)
        profile.save()
        messages.success(request, 'Address updated successfully!')
        return redirect('users:addresses')
    
    return render(request, 'users/addresses.html', {
        'profile': profile
    })


@login_required
def notifications_view(request):
    """User notifications view"""
    try:
        from promotions.models import UserNotification
        notifications = UserNotification.objects.filter(user=request.user).order_by('-created_at')
        unread_count = notifications.filter(is_read=False).count()
        
        # Mark notifications as read when viewed
        if request.GET.get('mark_read'):
            notifications.filter(is_read=False).update(is_read=True)
            return redirect('users:notifications')
    except:
        notifications = []
        unread_count = 0
    
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def invite_friends_view(request):
    """Invite friends feature"""
    if request.method == 'POST':
        emails = request.POST.get('emails', '').split(',')
        # Here you would implement email invitation logic
        messages.success(request, f'Invitations sent to {len(emails)} friends!')
        return redirect('users:dashboard')
    
    return render(request, 'users/invite_friends.html')


@login_required
def privacy_settings_view(request):
    """Handle privacy settings"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.is_public = request.POST.get('is_public') == 'on'
        profile.save()
        messages.success(request, 'Privacy settings updated successfully!')
        return redirect('users:profile')
    
    return redirect('users:profile')


@login_required
def change_password_view(request):
    """Handle password change"""
    from django.contrib.auth.forms import PasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Keeps user logged in
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})
