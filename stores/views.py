from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Sum, F
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from decimal import Decimal
import json

from .models import (
    Store, StoreApplication, StoreReview, StoreSubscription,
    StoreAnalytics, StoreNotification, StoreFollower, StoreCategory
)
from products.models import Product, Category, Brand
from orders.models import Order
from .forms import StoreApplicationForm, StoreForm, ProductForm


# Store Application Views
@login_required
def apply_for_store(request):
    """Apply to become a seller"""
    # Check if user already has a store or pending application
    if hasattr(request.user, 'store'):
        messages.info(request, 'You already have a store.')
        return redirect('stores:seller_dashboard')
    
    existing_application = StoreApplication.objects.filter(
        user=request.user, 
        status__in=['pending', 'under_review']
    ).first()
    
    if existing_application:
        messages.info(request, 'Your store application is under review.')
        return redirect('stores:application_status')
    
    if request.method == 'POST':
        form = StoreApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            
            messages.success(request, 'Your store application has been submitted successfully!')
            return redirect('stores:application_status')
    else:
        form = StoreApplicationForm()
    
    return render(request, 'stores/apply_for_store.html', {'form': form})


@login_required
def application_status(request):
    """Check application status"""
    try:
        application = StoreApplication.objects.get(user=request.user)
        return render(request, 'stores/application_status.html', {'application': application})
    except StoreApplication.DoesNotExist:
        messages.error(request, 'No application found.')
        return redirect('stores:apply_for_store')


# Seller Dashboard Views
@login_required
def seller_dashboard(request):
    """Main seller dashboard"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    # Get dashboard statistics
    today = timezone.now().date()
    
    # Products statistics
    total_products = store.products.count()
    active_products = store.products.filter(is_active=True).count()
    low_stock_products = store.products.filter(stock__lte=F('low_stock_threshold')).count()
    
    # Sales statistics (last 30 days)
    thirty_days_ago = today - timezone.timedelta(days=30)
    recent_orders = Order.objects.filter(
        items__product__store=store,
        created_at__date__gte=thirty_days_ago
    ).distinct()
    
    total_orders = recent_orders.count()
    total_revenue = recent_orders.aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0')
    
    # Recent notifications
    notifications = store.notifications.filter(is_read=False)[:5]
    
    # Recent reviews
    recent_reviews = store.reviews.order_by('-created_at')[:5]
    
    context = {
        'store': store,
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'notifications': notifications,
        'recent_reviews': recent_reviews,
    }
    
    return render(request, 'stores/seller_dashboard.html', context)


# Product Management Views
@login_required
def manage_products(request):
    """Manage store products"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    products = store.products.all().order_by('-created_at')
    
    # Search and filtering
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(sku__icontains=search)
        )
    
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    elif status_filter == 'low_stock':
        products = products.filter(stock__lte=F('low_stock_threshold'))
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'store': store,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'stores/manage_products.html', context)


@login_required
def add_product(request):
    """Add new product to store"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.store = store
            product.save()
            
            messages.success(request, f'Product "{product.name}" has been added successfully!')
            return redirect('stores:manage_products')
    else:
        form = ProductForm()
    
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'form': form,
        'categories': categories,
        'brands': brands,
        'store': store,
    }
    
    return render(request, 'stores/add_product.html', context)


@login_required
def edit_product(request, product_id):
    """Edit store product"""
    try:
        store = request.user.store
        product = get_object_or_404(Product, id=product_id, store=store)
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully!')
            return redirect('stores:manage_products')
    else:
        form = ProductForm(instance=product)
    
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'brands': brands,
        'store': store,
    }
    
    return render(request, 'stores/edit_product.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_product_status(request, product_id):
    """Toggle product active status"""
    try:
        store = request.user.store
        product = get_object_or_404(Product, id=product_id, store=store)
        product.is_active = not product.is_active
        product.save()
        
        status = "activated" if product.is_active else "deactivated"
        messages.success(request, f'Product "{product.name}" has been {status}.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_active': product.is_active,
                'message': f'Product {status} successfully.'
            })
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
    
    return redirect('stores:manage_products')


# Store Management Views
@login_required
def store_settings(request):
    """Store settings and profile"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store settings updated successfully!')
            return redirect('stores:store_settings')
    else:
        form = StoreForm(instance=store)
    
    context = {
        'form': form,
        'store': store,
    }
    
    return render(request, 'stores/store_settings.html', context)


@login_required
def store_analytics(request):
    """Store analytics and performance"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    # Date range (last 30 days by default)
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=30)
    
    # Get analytics data
    analytics_data = store.analytics.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Calculate totals
    total_sales = analytics_data.aggregate(Sum('daily_sales'))['daily_sales__sum'] or 0
    total_revenue = analytics_data.aggregate(Sum('daily_revenue'))['daily_revenue__sum'] or 0
    total_orders = analytics_data.aggregate(Sum('daily_orders'))['daily_orders__sum'] or 0
    total_views = analytics_data.aggregate(Sum('page_views'))['page_views__sum'] or 0
    
    # Best selling products
    best_products = store.products.filter(is_active=True).order_by('-sales_count')[:10]
    
    context = {
        'store': store,
        'analytics_data': analytics_data,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_views': total_views,
        'best_products': best_products,
        'date_range': f"{start_date} to {end_date}",
    }
    
    return render(request, 'stores/store_analytics.html', context)


# Public Store Views
def store_list(request):
    """List all active stores"""
    stores = Store.objects.filter(status='active').annotate(
        product_count=Count('products', filter=Q(products__is_active=True)),
        follower_count=Count('followers')
    ).order_by('-created_at')
    
    # Search and filtering
    search = request.GET.get('search')
    if search:
        stores = stores.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    category_filter = request.GET.get('category')
    if category_filter:
        stores = stores.filter(store_type=category_filter)
    
    # Pagination
    paginator = Paginator(stores, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'category_filter': category_filter,
        'store_types': Store.STORE_TYPE_CHOICES,
    }
    
    return render(request, 'stores/store_list.html', context)


def store_detail(request, slug):
    """Store detail page"""
    store = get_object_or_404(Store, slug=slug, status='active')
    
    # Get store products
    products = store.products.filter(is_active=True).order_by('-created_at')
    
    # Product filtering
    category_filter = request.GET.get('category')
    if category_filter:
        products = products.filter(category__slug=category_filter)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get store reviews
    reviews = store.reviews.order_by('-created_at')[:5]
    
    # Check if user follows this store
    is_following = False
    if request.user.is_authenticated:
        is_following = StoreFollower.objects.filter(
            store=store, user=request.user
        ).exists()
    
    # Get categories for filtering
    categories = Category.objects.filter(
        products__store=store,
        products__is_active=True
    ).distinct()
    
    context = {
        'store': store,
        'page_obj': page_obj,
        'reviews': reviews,
        'is_following': is_following,
        'categories': categories,
        'category_filter': category_filter,
    }
    
    return render(request, 'stores/store_detail.html', context)


@login_required
@require_http_methods(["POST"])
def follow_store(request, store_id):
    """Follow or unfollow a store"""
    store = get_object_or_404(Store, id=store_id, status='active')
    
    follower, created = StoreFollower.objects.get_or_create(
        store=store, user=request.user
    )
    
    if not created:
        follower.delete()
        is_following = False
        action = 'unfollowed'
    else:
        is_following = True
        action = 'followed'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'is_following': is_following,
            'message': f'You have {action} {store.name}.',
            'follower_count': store.followers.count()
        })
    
    messages.success(request, f'You have {action} {store.name}.')
    return redirect('stores:store_detail', slug=store.slug)


# Notification Views
@login_required
def notifications(request):
    """Store notifications"""
    try:
        store = request.user.store
    except Store.DoesNotExist:
        messages.error(request, 'You need to create a store first.')
        return redirect('stores:apply_for_store')
    
    notifications = store.notifications.order_by('-created_at')
    
    # Mark as read when viewed
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'store': store,
        'page_obj': page_obj,
    }
    
    return render(request, 'stores/notifications.html', context)
