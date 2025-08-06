
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from orders.models import Order
from .models import Payment
from django.contrib import messages
from .mpesa import MpesaDarajaAPI
from django.conf import settings


@staff_member_required
def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'payments/admin_payment_list.html', {'payments': payments})

@staff_member_required
def confirm_pi_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, payment_method='pi_coin')
    if request.method == 'POST':
        payment.pi_status = 'confirmed'
        payment.status = 'completed'
        payment.order.is_paid = True
        payment.order.save()
        payment.save()
        messages.success(request, 'Pi Coin payment confirmed.')
        return redirect('payments:admin_payment_list')
    return render(request, 'payments/confirm_pi_payment.html', {'payment': payment})

@login_required
def payment_history(request):
    payments = Payment.objects.filter(order__user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_history.html', {'payments': payments})

@login_required
def pay_order_pi(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user, is_paid=False)
    if request.method == 'POST':
        pi_wallet_address = request.POST.get('pi_wallet_address')
        amount = sum(item.price * item.quantity for item in order.items.all())
        # Here you would integrate with the Pi Network API or manual confirmation
        payment = Payment.objects.create(
            order=order,
            amount=amount,
            payment_method='pi_coin',
            pi_wallet_address=pi_wallet_address,
            pi_status='pending',
        )
        # In a real integration, you would update status after confirmation
        # For now, just show a message
        messages.success(request, 'Pi Coin payment initiated. Please complete the transfer and wait for confirmation.')
        return redirect('orders:order_detail', pk=order.pk)
    return render(request, 'payments/pay_order_pi.html', {'order': order})

@csrf_exempt
def mpesa_callback(request):
    # Handle M-Pesa payment confirmation callback
    import json
    data = json.loads(request.body.decode('utf-8'))
    result = data.get('Body', {}).get('stkCallback', {})
    checkout_id = result.get('CheckoutRequestID')
    result_code = result.get('ResultCode')
    try:
        from .models import Payment
        payment = Payment.objects.get(payment_id=checkout_id)
        if result_code == 0:
            payment.status = 'completed'
            payment.order.is_paid = True
            payment.order.save()
        else:
            payment.status = 'failed'
        payment.save()
    except Payment.DoesNotExist:
        pass
    return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})

@login_required
def pay_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user, is_paid=False)
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        amount = sum(item.price * item.quantity for item in order.items.all())
        # Initialize Daraja API
        mpesa = MpesaDarajaAPI(
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET,
            settings.MPESA_SHORTCODE,
            settings.MPESA_PASSKEY,
            settings.MPESA_BASE_URL
        )
        try:
            response = mpesa.stk_push(
                phone_number=phone_number,
                amount=int(amount),
                account_reference=f"Order{order.id}",
                transaction_desc=f"Payment for Order #{order.id}",
                callback_url="https://yourdomain.com/payments/mpesa-callback/"
            )
            Payment.objects.create(
                order=order,
                amount=amount,
                payment_method='mpesa',
                payment_id=response.get('CheckoutRequestID', ''),
                status='pending',
            )
            messages.success(request, 'M-Pesa payment initiated. Complete payment on your phone.')
            return redirect('orders:order_detail', pk=order.pk)
        except Exception as e:
            messages.error(request, f'Payment failed: {e}')
    return render(request, 'payments/pay_order.html', {'order': order})
