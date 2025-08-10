from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import ShippingMethod, ShippingRate, ShippingAddress, Tracking
from .forms import ShippingAddressForm
from orders.models import Order
import json


@login_required
def shipping_addresses(request):
    """Display user's shipping addresses"""
    addresses = ShippingAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
    
    context = {
        'addresses': addresses,
        'page_title': 'My Shipping Addresses'
    }
    return render(request, 'shipping/addresses.html', context)


@login_required
def add_shipping_address(request):
    """Add new shipping address"""
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            
            # If this is set as default, unset other default addresses
            if address.is_default:
                ShippingAddress.objects.filter(user=request.user).update(is_default=False)
            
            address.save()
            messages.success(request, 'Shipping address added successfully!')
            return redirect('shipping:addresses')
    else:
        form = ShippingAddressForm()
    
    context = {
        'form': form,
        'page_title': 'Add Shipping Address'
    }
    return render(request, 'shipping/add_address.html', context)


@login_required
def edit_shipping_address(request, address_id):
    """Edit shipping address"""
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST, instance=address)
        if form.is_valid():
            updated_address = form.save(commit=False)
            
            # If this is set as default, unset other default addresses
            if updated_address.is_default:
                ShippingAddress.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)
            
            updated_address.save()
            messages.success(request, 'Shipping address updated successfully!')
            return redirect('shipping:addresses')
    else:
        form = ShippingAddressForm(instance=address)
    
    context = {
        'form': form,
        'address': address,
        'page_title': 'Edit Shipping Address'
    }
    return render(request, 'shipping/edit_address.html', context)


@login_required
@require_http_methods(["POST"])
def delete_shipping_address(request, address_id):
    """Delete shipping address"""
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        address.delete()
        return JsonResponse({'success': True, 'message': 'Address deleted successfully!'})
    
    address.delete()
    messages.success(request, 'Shipping address deleted successfully!')
    return redirect('shipping:addresses')


@login_required
@require_http_methods(["POST"])
def set_default_address(request, address_id):
    """Set address as default"""
    address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    
    # Unset all other default addresses
    ShippingAddress.objects.filter(user=request.user).update(is_default=False)
    
    # Set this address as default
    address.is_default = True
    address.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Default address updated!'})
    
    messages.success(request, 'Default address updated!')
    return redirect('shipping:addresses')


def calculate_shipping(request):
    """Calculate shipping cost for cart"""
    if request.method == 'POST':
        data = json.loads(request.body)
        cart_weight = data.get('weight', 0)
        shipping_method_id = data.get('shipping_method_id')
        
        try:
            shipping_method = ShippingMethod.objects.get(id=shipping_method_id, is_active=True)
            shipping_rate = ShippingRate.objects.filter(
                shipping_method=shipping_method,
                min_weight__lte=cart_weight,
                max_weight__gte=cart_weight,
                is_active=True
            ).first()
            
            if shipping_rate:
                return JsonResponse({
                    'success': True,
                    'shipping_cost': float(shipping_rate.rate),
                    'estimated_days': shipping_method.estimated_days,
                    'method_name': shipping_method.name
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No shipping rate found for this weight'
                })
                
        except ShippingMethod.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Invalid shipping method'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def shipping_methods(request):
    """Get available shipping methods"""
    methods = ShippingMethod.objects.filter(is_active=True).order_by('estimated_days')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        methods_data = []
        for method in methods:
            methods_data.append({
                'id': method.id,
                'name': method.name,
                'provider': method.provider,
                'description': method.description,
                'estimated_days': method.estimated_days
            })
        return JsonResponse({'methods': methods_data})
    
    context = {
        'methods': methods,
        'page_title': 'Shipping Methods'
    }
    return render(request, 'shipping/methods.html', context)


@login_required
def track_order(request, order_id):
    """Track order shipment"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    try:
        tracking = Tracking.objects.get(order=order)
    except Tracking.DoesNotExist:
        tracking = None
    
    context = {
        'order': order,
        'tracking': tracking,
        'page_title': f'Track Order #{order.id}'
    }
    return render(request, 'shipping/track_order.html', context)


@login_required
def tracking_info(request, tracking_number):
    """Get tracking information by tracking number"""
    try:
        tracking = Tracking.objects.get(tracking_number=tracking_number)
        
        # Check if user owns this order
        if tracking.order.user != request.user:
            messages.error(request, 'You do not have permission to view this tracking information.')
            return redirect('core:home')
        
        context = {
            'tracking': tracking,
            'order': tracking.order,
            'page_title': f'Tracking #{tracking_number}'
        }
        return render(request, 'shipping/tracking_info.html', context)
        
    except Tracking.DoesNotExist:
        messages.error(request, 'Tracking number not found.')
        return redirect('core:home')


def shipping_zones(request):
    """Display shipping zones and rates"""
    methods = ShippingMethod.objects.filter(is_active=True).prefetch_related('rates')
    
    context = {
        'methods': methods,
        'page_title': 'Shipping Zones & Rates'
    }
    return render(request, 'shipping/zones.html', context)


@require_http_methods(["POST"])
def validate_shipping_address(request):
    """Validate shipping address via AJAX"""
    form = ShippingAddressForm(request.POST)
    
    if form.is_valid():
        return JsonResponse({'success': True, 'message': 'Address is valid'})
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@login_required
def shipping_calculator(request):
    """Shipping cost calculator page"""
    methods = ShippingMethod.objects.filter(is_active=True)
    
    context = {
        'methods': methods,
        'page_title': 'Shipping Calculator'
    }
    return render(request, 'shipping/calculator.html', context)
