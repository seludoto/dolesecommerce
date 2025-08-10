from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import F, Sum
from .models import FlashSale, FlashSaleProduct, FlashSalePurchase


def flash_sales_list(request):
    """List all active flash sales"""
    now = timezone.now()
    active_sales = FlashSale.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).prefetch_related('flashsaleproduct_set__product')
    
    upcoming_sales = FlashSale.objects.filter(
        is_active=True,
        start_time__gt=now
    ).order_by('start_time')[:3]
    
    context = {
        'active_sales': active_sales,
        'upcoming_sales': upcoming_sales,
    }
    
    return render(request, 'promotions/flash_sales.html', context)


def flash_sale_detail(request, flash_sale_id):
    """Flash sale detail page"""
    flash_sale = get_object_or_404(FlashSale, id=flash_sale_id)
    
    if not flash_sale.is_live:
        messages.warning(request, 'This flash sale is not currently active.')
        return redirect('promotions:flash_sales_list')
    
    products = flash_sale.flashsaleproduct_set.select_related('product').all()
    
    context = {
        'flash_sale': flash_sale,
        'products': products,
    }
    
    return render(request, 'promotions/flash_sale_detail.html', context)


@login_required
def add_flash_sale_to_cart(request, flash_sale_product_id):
    """Add flash sale product to cart"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    flash_sale_product = get_object_or_404(FlashSaleProduct, id=flash_sale_product_id)
    flash_sale = flash_sale_product.flash_sale
    
    if not flash_sale.is_live:
        return JsonResponse({'success': False, 'message': 'Flash sale is not active'})
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if user has already purchased max quantity
    user_purchases = FlashSalePurchase.objects.filter(
        user=request.user,
        flash_sale_product=flash_sale_product
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    if user_purchases + quantity > flash_sale.max_quantity_per_user:
        return JsonResponse({
            'success': False,
            'message': f'You can only buy {flash_sale.max_quantity_per_user} of this item'
        })
    
    # Check stock
    if flash_sale_product.sold_count + quantity > flash_sale_product.stock_limit:
        return JsonResponse({
            'success': False,
            'message': 'Not enough stock available'
        })
    
    try:
        # Add to cart (assuming you have cart functionality)
        from cart.models import Cart, CartItem
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=flash_sale_product.product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        # Record flash sale purchase
        FlashSalePurchase.objects.create(
            user=request.user,
            flash_sale_product=flash_sale_product,
            quantity=quantity
        )
        
        # Update sold count
        flash_sale_product.sold_count = F('sold_count') + quantity
        flash_sale_product.save()
        
        return JsonResponse({
            'success': True,
            'message': f'{flash_sale_product.product.name} added to cart',
            'cart_total_items': cart.total_items,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def get_flash_sale_time_remaining(request, flash_sale_id):
    """AJAX endpoint to get remaining time for flash sale"""
    flash_sale = get_object_or_404(FlashSale, id=flash_sale_id)
    
    if not flash_sale.is_live:
        return JsonResponse({'success': False, 'message': 'Sale ended'})
    
    time_remaining = flash_sale.time_remaining
    if time_remaining:
        total_seconds = int(time_remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        return JsonResponse({
            'success': True,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'total_seconds': total_seconds
        })
    
    return JsonResponse({'success': False, 'message': 'Sale ended'})
