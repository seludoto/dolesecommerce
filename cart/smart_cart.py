"""
Advanced Shopping Cart with AI-Powered Features
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Sum, F, Q
from decimal import Decimal
import json

from products.models import Product, ProductVariant
from core.recommendations import RecommendationEngine
from analytics.models import UserInteraction, ConversionFunnel
from .models import Cart, CartItem


class SmartCart:
    """AI-Powered Smart Shopping Cart"""
    
    def __init__(self, request):
        self.session = request.session
        self.user = request.user if request.user.is_authenticated else None
        self.cart_id = self._get_or_create_cart_id()
        self.rec_engine = RecommendationEngine()
    
    def _get_or_create_cart_id(self):
        """Get or create cart ID from session"""
        cart_id = self.session.get('cart_id')
        if not cart_id:
            cart_id = self.session.session_key
            if not cart_id:
                self.session.cycle_key()
                cart_id = self.session.session_key
            self.session['cart_id'] = cart_id
            self.session.modified = True
        return cart_id
    
    def add_item(self, product, quantity=1, variant=None, replace_quantity=False):
        """Add item to cart with smart recommendations"""
        try:
            if self.user:
                cart, created = Cart.objects.get_or_create(
                    user=self.user,
                    defaults={'session_id': self.cart_id}
                )
            else:
                cart, created = Cart.objects.get_or_create(
                    session_id=self.cart_id,
                    user=None
                )
            
            # Check if item already exists
            cart_item_qs = CartItem.objects.filter(
                cart=cart,
                product=product,
                variant=variant
            )
            
            if cart_item_qs.exists():
                cart_item = cart_item_qs.first()
                if replace_quantity:
                    cart_item.quantity = quantity
                else:
                    cart_item.quantity += quantity
                cart_item.save()
            else:
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    variant=variant,
                    quantity=quantity,
                    price=variant.price_adjustment + product.price if variant else product.price
                )
            
            # Track analytics
            if self.user:
                UserInteraction.objects.create(
                    user=self.user,
                    product=product,
                    interaction_type='add_to_cart',
                    session_id=self.cart_id
                )
                
                ConversionFunnel.objects.create(
                    user=self.user,
                    session_id=self.cart_id,
                    stage='add_to_cart',
                    product=product
                )
            
            return True, cart_item
            
        except Exception as e:
            return False, str(e)
    
    def remove_item(self, product, variant=None):
        """Remove item from cart"""
        try:
            if self.user:
                cart = Cart.objects.filter(user=self.user).first()
            else:
                cart = Cart.objects.filter(session_id=self.cart_id, user=None).first()
            
            if cart:
                CartItem.objects.filter(
                    cart=cart,
                    product=product,
                    variant=variant
                ).delete()
                
                # Track analytics
                if self.user:
                    UserInteraction.objects.create(
                        user=self.user,
                        product=product,
                        interaction_type='remove_from_cart',
                        session_id=self.cart_id
                    )
            
            return True
            
        except Exception as e:
            return False
    
    def update_quantity(self, product, quantity, variant=None):
        """Update item quantity in cart"""
        if quantity <= 0:
            return self.remove_item(product, variant)
        
        try:
            if self.user:
                cart = Cart.objects.filter(user=self.user).first()
            else:
                cart = Cart.objects.filter(session_id=self.cart_id, user=None).first()
            
            if cart:
                cart_item = CartItem.objects.filter(
                    cart=cart,
                    product=product,
                    variant=variant
                ).first()
                
                if cart_item:
                    cart_item.quantity = quantity
                    cart_item.save()
            
            return True
            
        except Exception as e:
            return False
    
    def get_cart_items(self):
        """Get all cart items"""
        try:
            if self.user:
                cart = Cart.objects.filter(user=self.user).first()
            else:
                cart = Cart.objects.filter(session_id=self.cart_id, user=None).first()
            
            if cart:
                return cart.items.select_related('product', 'variant').order_by('-created_at')
            return CartItem.objects.none()
            
        except Exception as e:
            return CartItem.objects.none()
    
    def get_cart_summary(self):
        """Get cart summary with totals"""
        items = self.get_cart_items()
        
        subtotal = sum(item.total_price for item in items)
        total_items = sum(item.quantity for item in items)
        
        # Calculate shipping (simplified)
        shipping = Decimal('0.00')
        if subtotal > 0 and subtotal < 50:  # Free shipping over $50
            shipping = Decimal('5.99')
        
        # Calculate tax (simplified)
        tax_rate = Decimal('0.08')  # 8% tax
        tax = subtotal * tax_rate
        
        total = subtotal + shipping + tax
        
        return {
            'items': items,
            'subtotal': subtotal,
            'shipping': shipping,
            'tax': tax,
            'total': total,
            'total_items': total_items,
            'item_count': items.count()
        }
    
    def get_recommendations(self):
        """Get AI-powered cart recommendations"""
        items = self.get_cart_items()
        
        if not items:
            return self.rec_engine.get_trending_products(8)
        
        # Get products in cart
        cart_products = [item.product for item in items]
        
        # Get frequently bought together items
        recommendations = []
        for product in cart_products:
            frequently_bought = self.rec_engine.get_frequently_bought_together(product, 3)
            recommendations.extend(frequently_bought)
        
        # Remove duplicates and products already in cart
        seen_ids = {product.id for product in cart_products}
        unique_recommendations = []
        
        for product in recommendations:
            if product.id not in seen_ids:
                unique_recommendations.append(product)
                seen_ids.add(product.id)
                if len(unique_recommendations) >= 6:
                    break
        
        # Fill with trending products if needed
        if len(unique_recommendations) < 6:
            trending = self.rec_engine.get_trending_products(10)
            for product in trending:
                if product.id not in seen_ids:
                    unique_recommendations.append(product)
                    if len(unique_recommendations) >= 6:
                        break
        
        return unique_recommendations[:6]
    
    def apply_discount_code(self, code):
        """Apply discount code to cart"""
        # Simplified discount system
        discount_codes = {
            'SAVE10': {'type': 'percentage', 'value': 10},
            'SAVE20': {'type': 'percentage', 'value': 20},
            'WELCOME5': {'type': 'fixed', 'value': 5},
        }
        
        if code.upper() in discount_codes:
            discount = discount_codes[code.upper()]
            self.session['discount_code'] = code.upper()
            self.session['discount'] = discount
            self.session.modified = True
            return True, discount
        
        return False, None
    
    def clear_cart(self):
        """Clear all items from cart"""
        try:
            if self.user:
                cart = Cart.objects.filter(user=self.user).first()
            else:
                cart = Cart.objects.filter(session_id=self.cart_id, user=None).first()
            
            if cart:
                cart.items.all().delete()
            
            # Clear session data
            if 'discount_code' in self.session:
                del self.session['discount_code']
            if 'discount' in self.session:
                del self.session['discount']
            self.session.modified = True
            
            return True
            
        except Exception as e:
            return False
    
    def merge_cart_on_login(self, user):
        """Merge anonymous cart with user cart on login"""
        try:
            # Get anonymous cart
            anonymous_cart = Cart.objects.filter(
                session_id=self.cart_id,
                user=None
            ).first()
            
            if not anonymous_cart:
                return
            
            # Get or create user cart
            user_cart, created = Cart.objects.get_or_create(
                user=user,
                defaults={'session_id': self.cart_id}
            )
            
            # Merge items
            for item in anonymous_cart.items.all():
                existing_item = user_cart.items.filter(
                    product=item.product,
                    variant=item.variant
                ).first()
                
                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                else:
                    item.cart = user_cart
                    item.save()
            
            # Delete anonymous cart
            anonymous_cart.delete()
            
        except Exception as e:
            pass


def cart_view(request):
    """Enhanced cart view with AI recommendations"""
    cart = SmartCart(request)
    cart_summary = cart.get_cart_summary()
    recommendations = cart.get_recommendations()
    
    # Get discount info
    discount_code = request.session.get('discount_code')
    discount = request.session.get('discount')
    
    # Calculate discount amount
    discount_amount = Decimal('0.00')
    if discount:
        if discount['type'] == 'percentage':
            discount_amount = cart_summary['subtotal'] * (Decimal(discount['value']) / 100)
        else:
            discount_amount = Decimal(discount['value'])
    
    # Update total with discount
    final_total = cart_summary['total'] - discount_amount
    
    context = {
        'cart_summary': cart_summary,
        'recommendations': recommendations,
        'discount_code': discount_code,
        'discount': discount,
        'discount_amount': discount_amount,
        'final_total': final_total,
    }
    
    return render(request, 'cart/cart.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def add_to_cart(request):
    """Add product to cart with AJAX support"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        variant = None
        
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        
        # Check stock
        available_stock = variant.stock if variant else product.stock
        if quantity > available_stock:
            return JsonResponse({
                'success': False,
                'message': f'Only {available_stock} items available in stock'
            })
        
        cart = SmartCart(request)
        success, result = cart.add_item(product, quantity, variant)
        
        if success:
            cart_summary = cart.get_cart_summary()
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_count': cart_summary['item_count'],
                'cart_total': str(cart_summary['total'])
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to add item to cart'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        })


@require_http_methods(["POST"])
@csrf_exempt
def update_cart_item(request):
    """Update cart item quantity"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')
        
        product = get_object_or_404(Product, id=product_id)
        variant = None
        
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
        
        cart = SmartCart(request)
        success = cart.update_quantity(product, quantity, variant)
        
        if success:
            cart_summary = cart.get_cart_summary()
            return JsonResponse({
                'success': True,
                'cart_count': cart_summary['item_count'],
                'cart_total': str(cart_summary['total']),
                'subtotal': str(cart_summary['subtotal'])
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update cart'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        })


@require_http_methods(["POST"])
@csrf_exempt
def remove_from_cart(request):
    """Remove item from cart"""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        
        product = get_object_or_404(Product, id=product_id)
        variant = None
        
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id)
        
        cart = SmartCart(request)
        success = cart.remove_item(product, variant)
        
        if success:
            cart_summary = cart.get_cart_summary()
            return JsonResponse({
                'success': True,
                'message': f'{product.name} removed from cart',
                'cart_count': cart_summary['item_count'],
                'cart_total': str(cart_summary['total']),
                'subtotal': str(cart_summary['subtotal'])
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove item'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred'
        })


@require_http_methods(["POST"])
def apply_discount(request):
    """Apply discount code"""
    discount_code = request.POST.get('discount_code', '').strip()
    
    if not discount_code:
        messages.error(request, 'Please enter a discount code')
        return redirect('cart:cart')
    
    cart = SmartCart(request)
    success, discount = cart.apply_discount_code(discount_code)
    
    if success:
        messages.success(request, f'Discount code \"{discount_code}\" applied successfully!')
    else:
        messages.error(request, 'Invalid discount code')
    
    return redirect('cart:cart')


def cart_count(request):
    """Get cart item count for AJAX"""
    cart = SmartCart(request)
    cart_summary = cart.get_cart_summary()
    
    return JsonResponse({
        'count': cart_summary['item_count'],
        'total': str(cart_summary['total'])
    })


def quick_add_to_cart(request, product_id):
    """Quick add to cart from product list"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Check stock
    if product.stock <= 0:
        messages.error(request, f'{product.name} is out of stock')
    else:
        cart = SmartCart(request)
        success, result = cart.add_item(product, 1)
        
        if success:
            messages.success(request, f'{product.name} added to cart')
        else:
            messages.error(request, 'Failed to add item to cart')
    
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def abandoned_cart_recovery(request):
    """Handle abandoned cart recovery from email links"""
    token = request.GET.get('token')
    
    # Simplified abandoned cart recovery
    # In a real implementation, you'd verify the token and restore the cart
    
    if token:
        messages.info(request, 'Your cart has been restored! Complete your purchase now.')
    
    return redirect('cart:cart')
