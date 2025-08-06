
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Order, OrderItem
from products.models import Product
from django.contrib import messages

# --- Buy Now Functionality ---
@login_required
@require_POST
def buy_now(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    order = Order.objects.create(user=request.user, shipping_address="")
    OrderItem.objects.create(order=order, product=product, quantity=1, price=product.price)
    messages.success(request, 'Order placed for product!')
    return redirect('orders:order_detail', pk=order.pk)

@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

# --- Cart Functionality ---
def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, pk=product_id)
        subtotal = product.price * quantity
        cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal
    return render(request, 'orders/cart_detail.html', {'cart_items': cart_items, 'total': total})

def cart_add(request, product_id):
    cart = request.session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, 'Product added to cart.')
    return redirect('orders:cart_detail')

def cart_remove(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, 'Product removed from cart.')
    return redirect('orders:cart_detail')

@login_required
def cart_checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Your cart is empty.')
        return redirect('orders:cart_detail')
    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address', '')
        order = Order.objects.create(user=request.user, shipping_address=shipping_address)
        for product_id, quantity in cart.items():
            product = get_object_or_404(Product, pk=product_id)
            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price)
        request.session['cart'] = {}
        messages.success(request, 'Order placed successfully!')
        return redirect('orders:order_detail', pk=order.pk)
    return render(request, 'orders/cart_checkout.html')
