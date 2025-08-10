#!/usr/bin/env python
"""
Quick fix script to ensure Pi payment tables exist and create initial rate
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dolesecommerce.settings')
django.setup()

def fix_pi_payment_setup():
    print("🔧 Fixing Pi Payment Setup...")
    
    try:
        # Import models
        from payments.models import PiCoinRate, Payment
        from decimal import Decimal
        
        print("✅ Models imported successfully")
        
        # Check if tables exist by trying a simple query
        try:
            count = PiCoinRate.objects.count()
            print(f"✅ PiCoinRate table exists with {count} records")
        except Exception as e:
            print(f"❌ PiCoinRate table issue: {e}")
            return False
        
        # Create default rate if none exists
        if not PiCoinRate.objects.filter(is_active=True).exists():
            rate = PiCoinRate.objects.create(
                pi_to_usd=Decimal('0.314159'),
                source='default_setup',
                is_active=True
            )
            print(f"✅ Created default Pi rate: 1π = ${rate.pi_to_usd} USD")
        else:
            current_rate = PiCoinRate.objects.filter(is_active=True).first()
            print(f"✅ Using existing rate: 1π = ${current_rate.pi_to_usd} USD")
        
        # Test conversion
        test_usd = Decimal('10.00')
        test_pi = PiCoinRate.convert_usd_to_pi(test_usd)
        print(f"✅ Test conversion: ${test_usd} = {test_pi:.7f}π")
        
        print("🎉 Pi Payment setup complete!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_pi_payment_setup()
    sys.exit(0 if success else 1)
