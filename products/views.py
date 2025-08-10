
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count, Min, Max, F
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from .models import Product, Category, Brand
import json


def product_list(request):
    """Enhanced product listing with filtering and search"""
    current_currency = request.session.get('currency', 'TZS')
    products = Product.objects.filter(is_active=True, currency=current_currency)
    
    # Search functionality
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )
    
    # Category filter
    category_slug = request.GET.get('category')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            pass
    
    # Brand filter
    brand_slug = request.GET.get('brand')
    if brand_slug:
        try:
            brand = Brand.objects.get(slug=brand_slug)
            products = products.filter(brand=brand)
        except Brand.DoesNotExist:
            pass
    
    # Price range filter
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except ValueError:
            pass
    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except ValueError:
            pass
    
    # Sorting
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-views_count', '-sales_count')
    else:  # featured/default
        products = products.order_by('-is_featured', '-views_count')
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Get filter options
    categories = Category.objects.filter(products__is_active=True).distinct()
    brands = Brand.objects.filter(products__is_active=True).distinct()
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    context = {
        'products': page_obj,
        'query': query,
        'categories': categories,
        'brands': brands,
        'price_range': price_range,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    """Enhanced product detail page"""
    product = get_object_or_404(Product, pk=pk, is_active=True)
    
    # Update view count
    Product.objects.filter(id=product.id).update(views_count=F('views_count') + 1)
    
    # Get similar products (fallback to category products)
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:8]
    
    # Get customer reviews (if reviews app is available)
    try:
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()
    except:
        reviews = []
        avg_rating = 0
        review_count = 0
    
    context = {
        'product': product,
        'similar_products': similar_products,
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    }
    
    return render(request, 'products/product_detail.html', context)


@login_required
@require_http_methods(["POST"])
def toggle_wishlist(request, product_id):
    """Toggle product in user's wishlist with AJAX support"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Simple response for now - wishlist feature will be implemented later
    message = f"{product.name} wishlist feature coming soon"
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': False,
            'message': message,
            'action': 'info',
            'wishlist_count': 0
        })
    
    messages.info(request, message)
    return redirect('products:product_detail', pk=product.pk)


def category_view(request, slug):
    """Enhanced category page with AI recommendations"""
    category = get_object_or_404(Category, slug=slug)
    
    # Get category products with smart sorting
    current_currency = request.session.get('currency', 'TZS')
    products = Product.objects.filter(
        category=category,
        is_active=True,
        currency=current_currency
    ).annotate(
        avg_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    )
    
    # Apply sorting
    sort_by = request.GET.get('sort', 'featured')
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'rating':
        products = products.order_by('-avg_rating', '-review_count')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        products = products.order_by('-is_featured', '-views_count', '-sales_count')
    
    # Pagination
    paginator = Paginator(products, 20)
    page = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page)
    except:
        page_obj = paginator.page(1)
    
    # Get featured products
    featured_products = products.filter(is_featured=True)[:8]
    
    # Get subcategories
    try:
        subcategories = category.subcategories.all()
    except:
        subcategories = []
    
    context = {
        'category': category,
        'products': page_obj,
        'featured_products': featured_products,
        'subcategories': subcategories,
        'sort_by': sort_by,
        'total_products': products.count(),
    }
    
    return render(request, 'products/category.html', context)


def api_search(request):
    """API endpoint for product search"""
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Limit results for API
    products = products[:20]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'price': float(product.price),
            'image': product.image.url if product.image else None,
            'url': f'/products/{product.id}/',
        })
    
    return JsonResponse({
        'results': results,
        'count': len(results)
    })
