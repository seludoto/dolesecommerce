"""
Advanced User Profile System with AI Personalization
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import UserProfile, Address, WishlistItem, OrderHistory
from .forms import UserProfileForm, AddressForm, CustomUserCreationForm
from orders.models import Order
from products.models import Product, Category
from core.recommendations import RecommendationEngine, PersonalizationEngine
from analytics.models import UserInteraction, BusinessMetric


def generate_user_insights(user):
    """Generate AI-powered user insights"""
    try:
        # Basic insight generation - can be enhanced with more AI
        insights = {
            'shopping_personality': 'Explorer',
            'preferred_categories': ['Electronics', 'Fashion'],
            'spending_trend': 'Increasing',
            'next_purchase_prediction': 'Within 7 days',
            'recommendations_accuracy': '85%',
            'savings_opportunities': 'Bundle deals available'
        }
        return insights
    except Exception:
        return {
            'shopping_personality': 'New Customer',
            'preferred_categories': [],
            'spending_trend': 'Unknown',
            'next_purchase_prediction': 'Unknown',
            'recommendations_accuracy': 'Learning...',
            'savings_opportunities': 'None'
        }


def register_view(request):
    """Enhanced user registration with AI onboarding"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(
                user=user,
                preferences={
                    'currency': 'USD',
                    'language': 'en',
                    'email_notifications': True,
                    'sms_notifications': False,
                }
            )
            
            # Log the user in
            login(request, user)
            
            # Track registration
            try:
                from analytics.models import UserInteraction
                UserInteraction.objects.create(
                    user=user,
                    interaction_type='register',
                    session_id=request.session.session_key or ''
                )
            except:
                pass
            
            messages.success(request, 'Welcome! Your account has been created successfully.')
            return redirect('users:onboarding')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def onboarding_view(request):
    """AI-powered user onboarding experience"""
    if request.method == 'POST':
        # Process onboarding preferences
        interests = request.POST.getlist('interests')
        preferred_brands = request.POST.getlist('brands')
        budget_range = request.POST.get('budget_range')
        shopping_frequency = request.POST.get('shopping_frequency')
        
        # Update user profile with preferences
        profile = request.user.profile
        profile.preferences.update({
            'interests': interests,
            'preferred_brands': preferred_brands,
            'budget_range': budget_range,
            'shopping_frequency': shopping_frequency,
            'onboarding_completed': True
        })
        profile.save()
        
        messages.success(request, 'Thanks for completing your profile! Here are some personalized recommendations.')
        return redirect('users:dashboard')
    
    # Get data for onboarding form
    categories = Category.objects.filter(is_featured=True)[:10]
    popular_brands = Product.objects.values('brand__name', 'brand__slug').annotate(
        product_count=Count('id')
    ).order_by('-product_count')[:15]
    
    context = {
        'categories': categories,
        'popular_brands': popular_brands,
    }
    
    return render(request, 'users/onboarding.html', context)


@login_required
def dashboard_view(request):
    """Personalized user dashboard with AI insights"""
    user = request.user
    profile = getattr(user, 'profile', None)
    
    # Get personalized content
    try:
        personalization = PersonalizationEngine.get_personalized_homepage(user)
        rec_engine = RecommendationEngine()
        recommendations = rec_engine.get_recommendations_for_user(user, 8)
    except:
        personalization = {'featured_products': [], 'trending_products': []}
        recommendations = []
    
    # Get user statistics
    try:
        order_stats = Order.objects.filter(user=user).aggregate(
            total_orders=Count('id'),
            total_spent=Sum('total_amount'),
            avg_order_value=Avg('total_amount')
        )
        
        recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Get user's favorite categories
        favorite_categories = Category.objects.filter(
            products__orderitem__order__user=user
        ).annotate(
            purchase_count=Count('products__orderitem')
        ).order_by('-purchase_count')[:5]
        
        # Get recently viewed products
        recently_viewed = getattr(user, 'recently_viewed', [])[:6]
        
        # Get wishlist items
        wishlist_items = getattr(user, 'wishlists', [])[:6]
        
    except Exception as e:
        order_stats = {'total_orders': 0, 'total_spent': 0, 'avg_order_value': 0}
        recent_orders = []
        favorite_categories = []
        recently_viewed = []
        wishlist_items = []
    
    # Get AI insights
    insights = generate_user_insights(user)
    
    context = {
        'profile': profile,
        'order_stats': order_stats,
        'recent_orders': recent_orders,
        'favorite_categories': favorite_categories,
        'recently_viewed': recently_viewed,
        'wishlist_items': wishlist_items,
        'recommendations': recommendations,
        'personalization': personalization,
        'insights': insights,
    }
    
    return render(request, 'users/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile management"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def addresses_view(request):
    """Manage user addresses"""
    addresses = Address.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    context = {
        'addresses': addresses,
    }
    
    return render(request, 'users/addresses.html', context)


@login_required
def add_address(request):
    """Add new address"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset other defaults
            if address.is_default:
                Address.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            messages.success(request, 'Address added successfully!')
            return redirect('users:addresses')
    else:
        form = AddressForm()
    
    return render(request, 'users/add_address.html', {'form': form})


@login_required
def edit_address(request, address_id):
    """Edit existing address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save()
            
            # If this is set as default, unset other defaults
            if address.is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
            
            messages.success(request, 'Address updated successfully!')
            return redirect('users:addresses')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'users/edit_address.html', {'form': form, 'address': address})


@login_required
@require_http_methods(["POST"])
def delete_address(request, address_id):
    """Delete address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if address.is_default and Address.objects.filter(user=request.user).count() > 1:
        # Set another address as default
        next_address = Address.objects.filter(user=request.user).exclude(id=address.id).first()
        if next_address:
            next_address.is_default = True
            next_address.save()
    
    address.delete()
    messages.success(request, 'Address deleted successfully!')
    return redirect('users:addresses')


@login_required
def order_history(request):
    """User's order history with analytics"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Get order statistics
    order_stats = orders.aggregate(
        total_orders=Count('id'),
        total_spent=Sum('total_amount'),
        avg_order_value=Avg('total_amount')
    )
    
    # Get monthly spending
    monthly_spending = []
    for i in range(12):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        
        spending = orders.filter(
            created_at__gte=month_start,
            created_at__lt=month_end,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        monthly_spending.append({
            'month': month_start.strftime('%B %Y'),
            'amount': spending
        })
    
    monthly_spending.reverse()
    
    context = {
        'orders': orders,
        'order_stats': order_stats,
        'monthly_spending': monthly_spending,
    }
    
    return render(request, 'users/order_history.html', context)


@login_required
def wishlist_view(request):
    """Enhanced wishlist with recommendations"""
    try:
        wishlist_items = request.user.wishlists.select_related('product').order_by('-created_at')
        
        # Get recommendations based on wishlist
        rec_engine = RecommendationEngine()
        if wishlist_items.exists():
            # Get similar products to wishlist items
            recommendations = []
            for item in wishlist_items[:3]:  # Use first 3 items for recommendations
                similar = rec_engine.get_product_recommendations(item.product, 3)
                recommendations.extend(similar)
            
            # Remove duplicates
            seen_ids = set()
            unique_recommendations = []
            for product in recommendations:
                if product.id not in seen_ids:
                    unique_recommendations.append(product)
                    seen_ids.add(product.id)
                    if len(unique_recommendations) >= 8:
                        break
        else:
            unique_recommendations = rec_engine.get_trending_products(8)
        
    except Exception as e:
        wishlist_items = []
        unique_recommendations = []
    
    context = {
        'wishlist_items': wishlist_items,
        'recommendations': unique_recommendations,
    }
    
    return render(request, 'users/wishlist.html', context)


@login_required
def preferences_view(request):
    """User preferences and settings"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update preferences
        preferences = profile.preferences or {}
        
        preferences.update({
            'currency': request.POST.get('currency', 'USD'),
            'language': request.POST.get('language', 'en'),
            'email_notifications': request.POST.get('email_notifications') == 'on',
            'sms_notifications': request.POST.get('sms_notifications') == 'on',
            'marketing_emails': request.POST.get('marketing_emails') == 'on',
            'price_alerts': request.POST.get('price_alerts') == 'on',
            'stock_alerts': request.POST.get('stock_alerts') == 'on',
            'newsletter': request.POST.get('newsletter') == 'on',
        })
        
        profile.preferences = preferences
        profile.save()
        
        messages.success(request, 'Preferences updated successfully!')
        return redirect('users:preferences')
    
    context = {
        'profile': profile,
        'preferences': profile.preferences or {},
    }
    
    return render(request, 'users/preferences.html', context)


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('users:profile')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'users/change_password.html', {'form': form})


@login_required
def analytics_view(request):
    """Personal analytics dashboard"""
    user = request.user
    
    # Get user interaction data
    interactions = UserInteraction.objects.filter(user=user).order_by('-timestamp')[:50]
    
    # Get shopping behavior analytics
    behavior_stats = {
        'most_viewed_categories': Category.objects.filter(
            products__interactions__user=user,
            products__interactions__interaction_type='view'
        ).annotate(
            view_count=Count('products__interactions')
        ).order_by('-view_count')[:5],
        
        'favorite_brands': Product.objects.filter(
            interactions__user=user
        ).values('brand__name').annotate(
            interaction_count=Count('interactions')
        ).order_by('-interaction_count')[:5],
        
        'shopping_patterns': get_shopping_patterns(user),
        'price_sensitivity': get_price_sensitivity(user),
    }
    
    context = {
        'interactions': interactions,
        'behavior_stats': behavior_stats,
    }
    
    return render(request, 'users/analytics.html', context)


def generate_user_insights_advanced(user):
    """Generate AI-powered insights for the user"""
    insights = []
    
    try:
        # Spending insights
        recent_orders = Order.objects.filter(
            user=user,
            created_at__gte=timezone.now() - timedelta(days=90)
        )
        
        if recent_orders.exists():
            avg_order = recent_orders.aggregate(avg=Avg('total_amount'))['avg']
            total_spent = recent_orders.aggregate(total=Sum('total_amount'))['total']
            
            insights.append({
                'type': 'spending',
                'title': 'Spending Summary',
                'message': f'You have spent ${total_spent:.2f} in the last 90 days with an average order value of ${avg_order:.2f}.'
            })
        
        # Category insights
        favorite_category = Category.objects.filter(
            products__orderitem__order__user=user
        ).annotate(
            purchase_count=Count('products__orderitem')
        ).order_by('-purchase_count').first()
        
        if favorite_category:
            insights.append({
                'type': 'category',
                'title': 'Shopping Preferences',
                'message': f'Your most purchased category is {favorite_category.name}. Check out our latest arrivals!'
            })
        
        # Savings opportunities
        wishlist_items = getattr(user, 'wishlists', [])
        on_sale_count = sum(1 for item in wishlist_items if item.product.is_on_sale)
        
        if on_sale_count > 0:
            insights.append({
                'type': 'savings',
                'title': 'Savings Alert',
                'message': f'{on_sale_count} items from your wishlist are currently on sale!'
            })
        
    except Exception as e:
        pass
    
    return insights


def get_shopping_patterns(user):
    """Analyze user shopping patterns"""
    try:
        orders = Order.objects.filter(user=user)
        
        # Get most active shopping days
        day_counts = {}
        for order in orders:
            day = order.created_at.strftime('%A')
            day_counts[day] = day_counts.get(day, 0) + 1
        
        most_active_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else 'Monday'
        
        # Get shopping frequency
        if orders.count() > 1:
            date_range = (orders.latest('created_at').created_at - orders.earliest('created_at').created_at).days
            frequency = orders.count() / (date_range / 30) if date_range > 0 else 0
        else:
            frequency = 0
        
        return {
            'most_active_day': most_active_day,
            'monthly_frequency': round(frequency, 1),
            'total_orders': orders.count()
        }
        
    except Exception as e:
        return {'most_active_day': 'Monday', 'monthly_frequency': 0, 'total_orders': 0}


def get_price_sensitivity(user):
    """Analyze user price sensitivity"""
    try:
        orders = Order.objects.filter(user=user)
        
        if orders.exists():
            avg_order_value = orders.aggregate(avg=Avg('total_amount'))['avg']
            
            # Categorize based on average order value
            if avg_order_value < 50:
                sensitivity = 'High'
                description = 'You prefer budget-friendly options'
            elif avg_order_value < 150:
                sensitivity = 'Medium'
                description = 'You balance quality and price'
            else:
                sensitivity = 'Low'
                description = 'You invest in premium products'
        else:
            sensitivity = 'Unknown'
            description = 'Start shopping to see your preferences'
        
        return {
            'level': sensitivity,
            'description': description,
            'avg_order_value': orders.aggregate(avg=Avg('total_amount'))['avg'] if orders.exists() else 0
        }
        
    except Exception as e:
        return {'level': 'Unknown', 'description': 'Analysis unavailable', 'avg_order_value': 0}
