
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
from .models import Payment
from .mpesa import MpesaDarajaAPI

logger = logging.getLogger(__name__)


@staff_member_required
def admin_payment_list(request):
    payments = Payment.objects.all().order_by('-created_at')
    return render(request, 'payments/admin_payment_list.html', {
        'payments': payments
    })


@login_required
def payment_history(request):
    payments = Payment.objects.filter(order__user=request.user).order_by('-created_at')
    return render(request, 'payments/payment_history.html', {'payments': payments})


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
    """Show available payment methods"""
    context = {
        'payment_methods': [
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
        ]
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
