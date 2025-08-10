#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dolesecommerce.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        # Check if PhonePayment table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments_phonepayment';")
        result = cursor.fetchone()
        if result:
            print("✓ payments_phonepayment table exists")
        else:
            print("✗ payments_phonepayment table does NOT exist")
        
        # List all payment tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'payments_%';")
        tables = cursor.fetchall()
        print("\nAll payment tables:")
        for table in tables:
            print(f"  - {table[0]}")

if __name__ == "__main__":
    try:
        check_tables()
    except Exception as e:
        print(f"Error: {e}")
