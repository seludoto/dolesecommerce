
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db import models
from decimal import Decimal
import json
import logging

from orders.models import Order
from .models import Payment, PiCoinRate, PiPaymentTransaction
from .mpesa import MpesaDarajaAPI
from .pi_network import pi_processor, PiNetworkError

logger = logging.getLogger(__name__)


@staff_member_required
def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-created_at')
    pi_payments = payments.filter(payment_method='pi_coin')
    return render(request, 'payments/admin_payment_list.html', {
        'payments': payments,
        'pi_payments': pi_payments
    })


@staff_member_required
def confirm_pi_payment(request, payment_id):
    payment = get_object_or_404(Payment, pk=payment_id, payment_method='pi_coin')
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'confirm':
            payment.pi_status = 'confirmed'
            payment.status = 'completed'
            payment.order.is_paid = True
            payment.order.save()
            payment.processed_by = request.user
            payment.save()
            messages.success(request, 'Pi Coin payment confirmed.')
        
        elif action == 'reject':
            payment.pi_status = 'rejected'
            payment.status = 'failed'
            payment.failure_reason = request.POST.get('reason', 'Payment rejected by admin')
            payment.processed_by = request.user
            payment.save()
            messages.warning(request, 'Pi Coin payment rejected.')
        
        return redirect('payments:admin_payment_list')
    
    return render(request, 'payments/confirm_pi_payment.html', {'payment': payment})


@staff_member_required
def pi_rate_management(request):
    """Manage Pi coin exchange rates"""
    if request.method == 'POST':
        rate = request.POST.get('pi_to_usd')
        source = request.POST.get('source', 'manual')
        
        try:
            rate_decimal = Decimal(rate)
            # Deactivate old rates
            PiCoinRate.objects.filter(is_active=True).update(is_active=False)
            # Create new rate
            PiCoinRate.objects.create(
                pi_to_usd=rate_decimal,
                source=source,
                is_active=True
            )
            messages.success(request, f'Pi coin rate updated to ${rate_decimal} USD')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid rate value')
    
    current_rate = PiCoinRate.get_current_rate()
    recent_rates = PiCoinRate.objects.all()[:10]
    
    return render(request, 'payments/pi_rate_management.html', {
        'current_rate': current_rate,
        'recent_rates': recent_rates
    })


@login_required
def payment_history(request):
    payments = Payment.objects.filter(order__user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_history.html', {'payments': payments})


@login_required
def pay_order_pi(request, order_id):
    """Process Pi Coin payment for an order"""
    order = get_object_or_404(Order, pk=order_id, user=request.user, is_paid=False)
    
    # Calculate amounts
    usd_amount = sum(item.price * item.quantity for item in order.items.all())
    
    # Get current rate or create default if none exists
    try:
        current_rate = PiCoinRate.get_current_rate()
    except:
        # Create default rate if none exists
        from decimal import Decimal
        PiCoinRate.objects.create(
            pi_to_usd=Decimal('0.314159'),
            source='default',
            is_active=True
        )
        current_rate = PiCoinRate.get_current_rate()
    
    pi_amount = PiCoinRate.convert_usd_to_pi(usd_amount)
    
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type', 'manual')
        
        if payment_type == 'api':
            # Use Pi Network API integration
            try:
                pi_response = pi_processor.initiate_payment(
                    order_id=str(order.id),
                    amount=pi_amount,
                    description=f"Payment for Order #{order.id}"
                )
                
                payment = Payment.objects.create(
                    order=order,
                    amount=usd_amount,
                    payment_method='pi_coin',
                    pi_payment_id=pi_response.get('identifier'),
                    pi_amount=pi_amount,
                    pi_exchange_rate=current_rate,
                    pi_status='api_initiated',
                    status='processing'
                )
                
                # Create transaction record
                PiPaymentTransaction.objects.create(
                    payment=payment,
                    pi_payment_id=pi_response.get('identifier'),
                    amount_pi=pi_amount,
                    amount_usd=usd_amount,
                    memo=f"Order #{order.id} payment"
                )
                
                payment.set_gateway_response_data(pi_response)
                payment.save()
                
                messages.success(request, 'Pi payment initiated through Pi Network API. Complete the payment in your Pi wallet.')
                return redirect('orders:order_detail', pk=order.pk)
                
            except PiNetworkError as e:
                messages.error(request, f'Pi Network API error: {e}')
            except Exception as e:
                logger.error(f"Pi payment initiation failed: {e}")
                messages.error(request, 'Failed to initiate Pi payment. Please try again.')
        
        else:
            # Manual Pi payment process
            pi_wallet_address = request.POST.get('pi_wallet_address', '').strip()
            
            if not pi_wallet_address:
                messages.error(request, 'Please provide your Pi wallet address.')
                return render(request, 'payments/pay_order_pi.html', {
                    'order': order,
                    'usd_amount': usd_amount,
                    'pi_amount': pi_amount,
                    'current_rate': current_rate
                })
            
            payment = Payment.objects.create(
                order=order,
                amount=usd_amount,
                payment_method='pi_coin',
                pi_wallet_address=pi_wallet_address,
                pi_amount=pi_amount,
                pi_exchange_rate=current_rate,
                pi_status='manual_pending',
                status='pending'
            )
            
            messages.success(request, 
                f'Pi payment request created. Please send {pi_amount:.7f} π to our wallet address and wait for confirmation.')
            return redirect('orders:order_detail', pk=order.pk)
    
    context = {
        'order': order,
        'usd_amount': usd_amount,
        'pi_amount': pi_amount,
        'current_rate': current_rate,
        'pi_wallet_address': getattr(settings, 'PI_WALLET_ADDRESS', 'GDQR...'),  # Your Pi wallet
        'pi_api_enabled': hasattr(settings, 'PI_NETWORK_API_KEY') and settings.PI_NETWORK_API_KEY
    }
    
    return render(request, 'payments/pay_order_pi.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def pi_payment_callback(request):
    """Handle Pi Network payment callbacks"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        logger.info(f"Pi payment callback received: {data}")
        
        # Process the callback
        result = pi_processor.process_payment_callback(data)
        payment_id = result.get('payment_id')
        
        if payment_id:
            try:
                payment = Payment.objects.get(pi_payment_id=payment_id)
                
                if result['success']:
                    payment.status = 'completed'
                    payment.pi_status = 'completed'
                    payment.order.is_paid = True
                    payment.order.save()
                    
                    # Update transaction record
                    transaction = payment.pi_transactions.first()
                    if transaction:
                        transaction.status = 'completed'
                        transaction.completed_at = timezone.now()
                        transaction.save()
                
                else:
                    payment.status = 'failed'
                    payment.pi_status = 'failed'
                    payment.failure_reason = result.get('message', 'Payment failed')
                
                payment.set_gateway_response_data(data)
                payment.save()
                
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for Pi payment ID: {payment_id}")
        
        return JsonResponse({"status": "success", "message": "Callback processed"})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in Pi payment callback")
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    
    except Exception as e:
        logger.error(f"Pi payment callback processing failed: {e}")
        return JsonResponse({"status": "error", "message": "Processing failed"}, status=500)


@login_required
@require_http_methods(["POST"])
def check_pi_payment_status(request, payment_id):
    """AJAX endpoint to check Pi payment status"""
    try:
        payment = get_object_or_404(Payment, pk=payment_id, order__user=request.user)
        
        if payment.is_pi_payment and payment.pi_payment_id:
            try:
                # Check status via Pi Network API
                pi_status = pi_processor.check_payment_status(payment.pi_payment_id)
                
                # Update payment status based on API response
                if pi_status.get('status') == 'completed':
                    payment.status = 'completed'
                    payment.pi_status = 'completed'
                    payment.order.is_paid = True
                    payment.order.save()
                    payment.save()
                
                return JsonResponse({
                    'status': payment.status,
                    'pi_status': payment.pi_status,
                    'message': 'Status updated from Pi Network'
                })
                
            except PiNetworkError as e:
                return JsonResponse({
                    'status': payment.status,
                    'pi_status': payment.pi_status,
                    'message': f'API Error: {e}'
                })
        
        return JsonResponse({
            'status': payment.status,
            'pi_status': payment.pi_status,
            'message': 'Current status'
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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


@login_required
def payment_methods(request):
    """Show available payment methods including Pi Coin"""
    pi_rate = PiCoinRate.get_current_rate()
    
    context = {
        'payment_methods': [
            {
                'id': 'pi_coin',
                'name': 'Pi Coin',
                'description': 'Pay with Pi cryptocurrency',
                'icon': 'fab fa-bitcoin',
                'rate': f'1 π = ${pi_rate} USD',
                'fees': '0% transaction fee'
            },
            {
                'id': 'mpesa',
                'name': 'M-Pesa',
                'description': 'Mobile money payment',
                'icon': 'fas fa-mobile-alt',
                'fees': 'Standard M-Pesa rates apply'
            },
            {
                'id': 'credit_card',
                'name': 'Credit/Debit Card',
                'description': 'Visa, Mastercard, Amex',
                'icon': 'fas fa-credit-card',
                'fees': '2.9% + $0.30 per transaction'
            }
        ],
        'pi_rate': pi_rate
    }
    
    return render(request, 'payments/payment_methods.html', context)


# Phone Payment Views
@staff_member_required
def phone_payment_dashboard(request):
    """Dashboard for managing phone payments"""
    from .models import PhonePayment, MpesaB2CTransaction, MpesaC2BTransaction
    
    # Get recent phone payments
    phone_payments = PhonePayment.objects.all()[:20]
    
    # Get recent transactions
    b2c_transactions = MpesaB2CTransaction.objects.all()[:10]
    c2b_transactions = MpesaC2BTransaction.objects.all()[:10]
    
    # Statistics
    total_sent = PhonePayment.objects.filter(
        payment_type='send', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    total_received = PhonePayment.objects.filter(
        payment_type='receive', 
        status='completed'
    ).aggregate(total=models.Sum('amount'))['total'] or 0
    
    context = {
        'phone_payments': phone_payments,
        'b2c_transactions': b2c_transactions,
        'c2b_transactions': c2b_transactions,
        'total_sent': total_sent,
        'total_received': total_received,
    }
    
    return render(request, 'payments/phone_payment_dashboard.html', context)


@staff_member_required
def send_money_to_phone(request):
    """Send money directly to a phone number"""
    from .models import PhonePayment, MpesaB2CTransaction
    from .mpesa import get_mpesa_processor
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        amount = request.POST.get('amount', '').strip()
        description = request.POST.get('description', '').strip()
        
        try:
            # Validate inputs
            if not phone_number or not amount or not description:
                raise ValueError("All fields are required")
            
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
            
            # Format phone number
            mpesa_processor = get_mpesa_processor()
            formatted_phone = mpesa_processor.api.format_phone_number(phone_number)
            if not mpesa_processor.api.validate_phone_number(formatted_phone):
                raise ValueError("Invalid phone number format")
            
            # Create phone payment record
            phone_payment = PhonePayment.objects.create(
                payment_type='send',
                provider='mpesa',
                phone_number=formatted_phone,
                amount=amount_decimal,
                description=description,
                initiated_by=request.user,
                status='processing'
            )
            
            # Send money via M-Pesa B2C
            result = mpesa_processor.send_money_to_phone(
                phone_number=formatted_phone,
                amount=amount_decimal,
                description=description
            )
            
            # Create B2C transaction record
            b2c_transaction = MpesaB2CTransaction.objects.create(
                conversation_id=result.get('ConversationID', ''),
                originator_conversation_id=result.get('OriginatorConversationID', ''),
                phone_number=formatted_phone,
                amount=amount_decimal,
                remarks=description,
                status='initiated',
                response_code=result.get('ResponseCode', ''),
                response_description=result.get('ResponseDescription', '')
            )
            
            # Link the transactions
            phone_payment.mpesa_b2c = b2c_transaction
            phone_payment.transaction_id = b2c_transaction.conversation_id
            phone_payment.save()
            
            messages.success(request, f'Money sent successfully to {formatted_phone}. Transaction ID: {b2c_transaction.conversation_id}')
            return redirect('payments:phone_payment_dashboard')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Failed to send money to phone: {e}")
            messages.error(request, f'Failed to send money: {str(e)}')
    
    return render(request, 'payments/send_money_to_phone.html')


@staff_member_required  
def request_payment_from_phone(request):
    """Request payment from a phone number via STK Push"""
    from .models import PhonePayment, MpesaC2BTransaction
    from .mpesa import get_mpesa_processor
    
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number', '').strip()
        amount = request.POST.get('amount', '').strip()
        description = request.POST.get('description', '').strip()
        reference = request.POST.get('reference', '').strip()
        
        try:
            # Validate inputs
            if not phone_number or not amount or not description:
                raise ValueError("Phone number, amount, and description are required")
            
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
            
            # Format phone number
            mpesa_processor = get_mpesa_processor()
            formatted_phone = mpesa_processor.api.format_phone_number(phone_number)
            if not mpesa_processor.api.validate_phone_number(formatted_phone):
                raise ValueError("Invalid phone number format")
            
            # Create phone payment record
            phone_payment = PhonePayment.objects.create(
                payment_type='receive',
                provider='mpesa',
                phone_number=formatted_phone,
                amount=amount_decimal,
                description=description,
                initiated_by=request.user,
                status='processing'
            )
            
            # Use reference if provided, otherwise use phone payment reference
            order_reference = reference or phone_payment.reference
            
            # Request payment via STK Push
            result = mpesa_processor.request_payment_from_phone(
                phone_number=formatted_phone,
                amount=amount_decimal,
                order_reference=order_reference,
                description=description
            )
            
            # Create C2B transaction record
            c2b_transaction = MpesaC2BTransaction.objects.create(
                checkout_request_id=result.get('CheckoutRequestID', ''),
                merchant_request_id=result.get('MerchantRequestID', ''),
                phone_number=formatted_phone,
                amount=amount_decimal,
                account_reference=order_reference,
                transaction_desc=description,
                status='initiated'
            )
            
            # Link the transactions
            phone_payment.mpesa_c2b = c2b_transaction
            phone_payment.transaction_id = c2b_transaction.checkout_request_id
            phone_payment.save()
            
            messages.success(request, f'Payment request sent to {formatted_phone}. Customer will receive STK push.')
            return redirect('payments:phone_payment_dashboard')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Failed to request payment from phone: {e}")
            messages.error(request, f'Failed to request payment: {str(e)}')
    
    return render(request, 'payments/request_payment_from_phone.html')


@csrf_exempt
@require_http_methods(["POST"])
def mpesa_b2c_result_callback(request):
    """Handle M-Pesa B2C result callback"""
    from .models import MpesaB2CTransaction
    
    try:
        data = json.loads(request.body)
        result = data.get('Result', {})
        
        conversation_id = result.get('ConversationID', '')
        result_code = result.get('ResultCode', '')
        result_desc = result.get('ResultDesc', '')
        
        # Find the transaction
        try:
            transaction = MpesaB2CTransaction.objects.get(conversation_id=conversation_id)
            
            # Update transaction status
            if result_code == '0':
                transaction.status = 'completed'
                transaction.response_code = result_code
                transaction.response_description = result_desc
                
                # Extract additional details from result parameters
                result_parameters = result.get('ResultParameters', {}).get('ResultParameter', [])
                for param in result_parameters:
                    key = param.get('Key', '')
                    value = param.get('Value', '')
                    
                    if key == 'TransactionID':
                        transaction.transaction_id = value
                    elif key == 'TransactionReceipt':
                        transaction.transaction_receipt = value
                    elif key == 'ReceiverPartyPublicName':
                        transaction.receiver_party_public_name = value
                    elif key == 'TransactionCompletedDateTime':
                        from datetime import datetime
                        try:
                            transaction.transaction_completed_date_time = datetime.strptime(
                                value, '%d.%m.%Y %H:%M:%S'
                            )
                        except:
                            pass
                    elif key == 'B2CChargesPaidAccountAvailableFunds':
                        try:
                            transaction.b2c_charges_paid_account_available_funds = Decimal(value)
                        except:
                            pass
                    elif key == 'B2CUtilityAccountAvailableFunds':
                        try:
                            transaction.b2c_utility_account_available_funds = Decimal(value)
                        except:
                            pass
                    elif key == 'B2CWorkingAccountAvailableFunds':
                        try:
                            transaction.b2c_working_account_available_funds = Decimal(value)
                        except:
                            pass
                
                # Update related phone payment
                if hasattr(transaction, 'phonepayment'):
                    phone_payment = transaction.phonepayment
                    phone_payment.status = 'completed'
                    phone_payment.receipt_number = transaction.transaction_receipt
                    phone_payment.completed_at = timezone.now()
                    phone_payment.save()
                    
            else:
                transaction.status = 'failed'
                transaction.response_code = result_code
                transaction.response_description = result_desc
                
                # Update related phone payment
                if hasattr(transaction, 'phonepayment'):
                    phone_payment = transaction.phonepayment
                    phone_payment.status = 'failed'
                    phone_payment.save()
            
            transaction.save()
            logger.info(f"B2C transaction {conversation_id} updated: {result_desc}")
            
        except MpesaB2CTransaction.DoesNotExist:
            logger.warning(f"B2C transaction not found: {conversation_id}")
        
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        
    except Exception as e:
        logger.error(f"B2C callback error: {e}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})


@csrf_exempt  
@require_http_methods(["POST"])
def mpesa_b2c_timeout_callback(request):
    """Handle M-Pesa B2C timeout callback"""
    try:
        data = json.loads(request.body)
        result = data.get('Result', {})
        conversation_id = result.get('ConversationID', '')
        
        logger.warning(f"B2C transaction timeout: {conversation_id}")
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        
    except Exception as e:
        logger.error(f"B2C timeout callback error: {e}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
