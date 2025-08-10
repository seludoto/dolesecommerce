from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from .models import Cart, CartItem, SavedForLater, PromoCode, CartPromoCode, CartRecommendation
from products.models import Product, RecentlyViewed
import json
from decimal import Decimal


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart


def cart_detail(request):
    """Enhanced cart detail view with recommendations and advanced features"""
    cart = get_or_create_cart(request)
    
    # Get saved items for authenticated users
    saved_items = []
    if request.user.is_authenticated:
        saved_items = SavedForLater.objects.filter(user=request.user)
    
    # Get recently viewed products
    recently_viewed = []
    if request.user.is_authenticated:
        recently_viewed = RecentlyViewed.objects.filter(
            user=request.user
        ).order_by('-viewed_at')[:4]
    
    # Generate product recommendations
    recommended_products = get_cart_recommendations(cart)
    
    # Get applied promo codes
    applied_promos = CartPromoCode.objects.filter(cart=cart)
    
    context = {
        'cart': cart,
        'saved_items': saved_items,
        'recently_viewed': recently_viewed,
        'recommended_products': recommended_products,
        'applied_promos': applied_promos,
    }
    
    return render(request, 'cart/cart_detail.html', context)


def get_cart_recommendations(cart):
    """Generate AI-powered product recommendations for the cart"""
    if not cart.items.exists():
        # Return trending products for empty cart
        return Product.objects.filter(is_active=True).order_by('-sales_count')[:4]
    
    # Get categories of items in cart
    cart_categories = set()
    cart_brands = set()
    
    for item in cart.items.all():
        if hasattr(item.product, 'category'):
            cart_categories.add(item.product.category)
        if hasattr(item.product, 'brand'):
            cart_brands.add(item.product.brand)
    
    # Find frequently bought together products
    recommended_products = Product.objects.filter(
        is_active=True
    ).exclude(
        id__in=[item.product.id for item in cart.items.all()]
    )
    
    if cart_categories:
        recommended_products = recommended_products.filter(
            category__in=cart_categories
        )
    
    # Order by sales count and rating
    recommended_products = recommended_products.annotate(
        avg_rating=Avg('reviews__rating')
    ).order_by('-sales_count', '-avg_rating')[:6]
    
    return recommended_products


@require_POST
def add_to_cart(request):
    """Add product to cart with advanced options"""
    try:
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        size = request.POST.get('size', '')
        color = request.POST.get('color', '')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart = get_or_create_cart(request)
        
        # Check stock availability
        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {product.stock} items available in stock'
            })
        
        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            color=color,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot add {quantity} more. Only {product.stock - cart_item.quantity} available'
                })
            cart_item.quantity = new_quantity
            cart_item.save()
        
        # Update product sales count
        product.sales_count += quantity
        product.save()
        
        # Generate recommendations for this cart
        generate_cart_recommendations(cart)
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} added to cart',
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def generate_cart_recommendations(cart):
    """Generate and store cart recommendations"""
    # Clear existing recommendations
    CartRecommendation.objects.filter(cart=cart).delete()
    
    recommended_products = get_cart_recommendations(cart)
    
    for i, product in enumerate(recommended_products):
        CartRecommendation.objects.create(
            cart=cart,
            recommended_product=product,
            recommendation_type='FREQUENTLY_BOUGHT',
            confidence_score=1.0 - (i * 0.1)  # Decreasing confidence
        )


@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        quantity = int(request.POST.get('quantity', 1))
        
        # Verify cart ownership
        cart = get_or_create_cart(request)
        if cart_item.cart != cart:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        # Check stock
        if quantity > cart_item.product.stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.product.stock} items available'
            })
        
        if quantity <= 0:
            cart_item.delete()
            message = 'Item removed from cart'
        else:
            cart_item.quantity = quantity
            cart_item.save()
            message = 'Cart updated successfully'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def remove_cart_item(request, item_id):
    """Remove item from cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart = get_or_create_cart(request)
        
        if cart_item.cart != cart:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        product_name = cart_item.product.name
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} removed from cart',
            'cart_total_items': cart.total_items,
            'cart_total_price': float(cart.total_price)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def save_for_later(request, item_id):
    """Save cart item for later"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id)
        cart = get_or_create_cart(request)
        
        if cart_item.cart != cart:
            return JsonResponse({'success': False, 'message': 'Unauthorized'})
        
        # Create saved item
        saved_item, created = SavedForLater.objects.get_or_create(
            user=request.user,
            product=cart_item.product,
            size=cart_item.size,
            color=cart_item.color
        )
        
        # Remove from cart
        product_name = cart_item.product.name
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} saved for later',
            'cart_total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_POST
def move_to_cart(request, product_id):
    """Move saved item back to cart"""
    try:
        saved_item = get_object_or_404(
            SavedForLater, 
            user=request.user, 
            product_id=product_id
        )
        
        cart = get_or_create_cart(request)
        
        # Check stock
        if saved_item.product.stock <= 0:
            return JsonResponse({
                'success': False,
                'message': 'Product is out of stock'
            })
        
        # Add to cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=saved_item.product,
            size=saved_item.size,
            color=saved_item.color,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        # Remove from saved
        product_name = saved_item.product.name
        saved_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{product_name} moved to cart',
            'cart_total_items': cart.total_items
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def apply_promo_code(request):
    """Apply promotional code to cart"""
    try:
        promo_code = request.POST.get('promo_code', '').upper().strip()
        cart = get_or_create_cart(request)
        
        if not promo_code:
            return JsonResponse({'success': False, 'message': 'Please enter a promo code'})
        
        # Check if code exists and is valid
        try:
            promo = PromoCode.objects.get(code=promo_code)
        except PromoCode.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid promo code'})
        
        if not promo.is_valid:
            return JsonResponse({'success': False, 'message': 'Promo code has expired or is not active'})
        
        # Check if already applied
        if CartPromoCode.objects.filter(cart=cart, promo_code=promo).exists():
            return JsonResponse({'success': False, 'message': 'Promo code already applied'})
        
        # Check minimum order requirement
        if cart.total_price < promo.minimum_order:
            return JsonResponse({
                'success': False,
                'message': f'Minimum order of ${promo.minimum_order} required'
            })
        
        # Check first-time user restriction
        if promo.first_time_users_only and request.user.is_authenticated:
            from orders.models import Order
            if Order.objects.filter(user=request.user).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'This promo code is for first-time customers only'
                })
        
        # Calculate discount
        discount_amount = promo.calculate_discount(cart.total_price)
        
        if discount_amount <= 0:
            return JsonResponse({'success': False, 'message': 'Promo code cannot be applied to this order'})
        
        # Apply promo code
        CartPromoCode.objects.create(
            cart=cart,
            promo_code=promo,
            discount_amount=discount_amount
        )
        
        # Update usage count
        promo.used_count += 1
        promo.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Promo code applied! You saved ${discount_amount}',
            'discount_amount': float(discount_amount),
            'new_total': float(cart.final_total)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@require_POST
def remove_promo_code(request, promo_id):
    """Remove promo code from cart"""
    try:
        cart = get_or_create_cart(request)
        cart_promo = get_object_or_404(CartPromoCode, id=promo_id, cart=cart)
        
        # Decrease usage count
        promo = cart_promo.promo_code
        promo.used_count = max(0, promo.used_count - 1)
        promo.save()
        
        cart_promo.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Promo code removed',
            'new_total': float(cart.final_total)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def cart_recovery(request, token):
    """Recover abandoned cart from email link"""
    try:
        from .models import AbandonedCart
        abandoned_cart = get_object_or_404(AbandonedCart, recovery_token=token)
        
        if abandoned_cart.recovered:
            messages.info(request, 'This cart has already been recovered.')
            return redirect('cart:cart_detail')
        
        # Restore cart items
        cart = get_or_create_cart(request)
        cart_data = abandoned_cart.cart_data
        
        for item_data in cart_data.get('items', []):
            try:
                product = Product.objects.get(id=item_data['product_id'])
                if product.is_active and product.stock >= item_data['quantity']:
                    CartItem.objects.get_or_create(
                        cart=cart,
                        product=product,
                        size=item_data.get('size', ''),
                        color=item_data.get('color', ''),
                        defaults={'quantity': item_data['quantity']}
                    )
            except Product.DoesNotExist:
                continue
        
        # Mark as recovered
        abandoned_cart.recovered = True
        abandoned_cart.recovered_at = timezone.now()
        abandoned_cart.save()
        
        messages.success(request, 'Your cart has been restored!')
        return redirect('cart:cart_detail')
        
    except Exception as e:
        messages.error(request, 'Unable to recover cart.')
        return redirect('cart:cart_detail')


def get_cart_count(request):
    """Get cart item count for AJAX requests"""
    cart = get_or_create_cart(request)
    return JsonResponse({'count': cart.total_items})


@login_required
def clear_cart(request):
    """Clear all items from cart"""
    if request.method == 'POST':
        cart = get_or_create_cart(request)
        cart.clear_cart()
        messages.success(request, 'Cart cleared successfully!')
    
    return redirect('cart:cart_detail')
