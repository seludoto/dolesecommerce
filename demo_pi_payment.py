"""
Pi Coin Payment System Demo
This script demonstrates the Pi Coin payment functionality
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dolesecommerce.settings')
django.setup()

from decimal import Decimal
from datetime import datetime
from payments.models import Payment, PiCoinRate, PiPaymentTransaction
from payments.pi_network import pi_processor, PiNetworkError
from orders.models import Order
from django.contrib.auth.models import User

def demo_pi_payment_system():
    """Demonstrate the Pi payment system functionality"""
    
    print("🔄 Pi Coin Payment System Demo")
    print("=" * 50)
    
    # 1. Initialize Pi rates
    print("\n1. Setting up Pi exchange rates...")
    
    # Deactivate existing rates
    PiCoinRate.objects.filter(is_active=True).update(is_active=False)
    
    # Create new rate
    pi_rate = PiCoinRate.objects.create(
        pi_to_usd=Decimal('0.314159'),
        source='demo',
        is_active=True
    )
    
    print(f"   ✅ Pi rate set: 1 π = ${pi_rate.pi_to_usd} USD")
    
    # 2. Create test user and order (if they don't exist)
    print("\n2. Creating test data...")
    
    try:
        user = User.objects.get(username='pi_test_user')
        print(f"   ✅ Using existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='pi_test_user',
            email='pi_test@example.com',
            password='testpass123'
        )
        print(f"   ✅ Created test user: {user.username}")
    
    # 3. Demonstrate Pi rate conversion
    print("\n3. Testing Pi rate conversions...")
    
    test_amounts = [10.00, 25.50, 100.00, 500.00]
    
    for usd_amount in test_amounts:
        pi_amount = PiCoinRate.convert_usd_to_pi(Decimal(str(usd_amount)))
        usd_back = PiCoinRate.convert_pi_to_usd(pi_amount)
        
        print(f"   ${usd_amount:>7.2f} USD = {pi_amount:>12.7f} π = ${usd_back:>7.2f} USD")
    
    # 4. Simulate Pi payment creation
    print("\n4. Simulating Pi payment creation...")
    
    try:
        # Create mock payment data
        mock_payment_data = {
            'amount_usd': Decimal('50.00'),
            'pi_amount': PiCoinRate.convert_usd_to_pi(Decimal('50.00')),
            'description': 'Demo Pi Payment',
            'order_id': 'DEMO_001'
        }
        
        print(f"   Payment Amount: ${mock_payment_data['amount_usd']} USD")
        print(f"   Pi Amount: {mock_payment_data['pi_amount']:.7f} π")
        print(f"   Description: {mock_payment_data['description']}")
        
        # Simulate API call
        print("\n   Simulating Pi Network API call...")
        print("   📞 Calling pi_processor.initiate_payment()...")
        
        # Mock response (since we don't have real API credentials)
        mock_response = {
            'identifier': 'PI_DEMO_' + str(int(datetime.now().timestamp())),
            'status': 'initiated',
            'amount': float(mock_payment_data['pi_amount']),
            'memo': mock_payment_data['description']
        }
        
        print(f"   ✅ Mock API Response: {mock_response}")
        
    except Exception as e:
        print(f"   ⚠️  API simulation error: {e}")
    
    # 5. Show Pi payment statistics
    print("\n5. Pi Payment Statistics:")
    
    total_payments = Payment.objects.count()
    pi_payments = Payment.objects.filter(payment_method='pi_coin').count()
    pi_rates_count = PiCoinRate.objects.count()
    
    print(f"   Total Payments: {total_payments}")
    print(f"   Pi Payments: {pi_payments}")
    print(f"   Pi Rates Configured: {pi_rates_count}")
    
    # 6. Show available payment methods
    print("\n6. Available Payment Methods:")
    
    payment_methods = [
        ('pi_coin', 'Pi Coin', '🔹 π'),
        ('mpesa', 'M-Pesa', '📱'),
        ('credit_card', 'Credit Card', '💳'),
        ('bank_transfer', 'Bank Transfer', '🏦'),
    ]
    
    for method, name, icon in payment_methods:
        print(f"   {icon} {name} ({method})")
    
    # 7. Display Pi Network configuration
    print("\n7. Pi Network Configuration:")
    
    from django.conf import settings
    
    config_items = [
        ('PI_NETWORK_API_KEY', getattr(settings, 'PI_NETWORK_API_KEY', 'Not set')),
        ('PI_WALLET_ADDRESS', getattr(settings, 'PI_WALLET_ADDRESS', 'Not set')),
        ('PI_SANDBOX_MODE', getattr(settings, 'PI_SANDBOX_MODE', True)),
        ('PI_DEFAULT_RATE', getattr(settings, 'PI_DEFAULT_RATE', 0.314159)),
    ]
    
    for key, value in config_items:
        masked_value = value
        if 'KEY' in key and value != 'Not set':
            masked_value = f"{value[:8]}..." if len(str(value)) > 8 else value
        print(f"   {key}: {masked_value}")
    
    # 8. Show integration URLs
    print("\n8. Pi Payment URLs:")
    
    urls = [
        '/payments/pay/pi/<order_id>/',
        '/payments/pi/callback/',
        '/payments/pi/status/<payment_id>/',
        '/payments/admin/pi-rates/',
        '/payments/methods/',
    ]
    
    for url in urls:
        print(f"   🔗 {url}")
    
    print("\n" + "=" * 50)
    print("✅ Pi Coin Payment System Demo Complete!")
    print("\nKey Features Implemented:")
    print("• 🔹 Pi Network API integration")
    print("• 💱 Real-time exchange rate management")
    print("• 🎯 Manual and automatic payment processing")
    print("• 🛡️  Secure payment verification")
    print("• 📊 Comprehensive admin interface")
    print("• 📱 Mobile-responsive payment forms")
    print("• 🔄 Payment status tracking")
    print("• 📈 Payment analytics and reporting")
    
    print("\nNext Steps:")
    print("1. Configure real Pi Network API credentials")
    print("2. Set up webhook endpoints for payment callbacks")
    print("3. Test with actual Pi transactions")
    print("4. Deploy to production environment")
    
    return True

if __name__ == '__main__':
    try:
        demo_pi_payment_system()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
