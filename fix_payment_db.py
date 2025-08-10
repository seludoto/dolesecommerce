#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dolesecommerce.settings')
django.setup()

from django.core.management.color import no_style
from django.db import connection
from payments.models import PhonePayment, MpesaB2CTransaction, MpesaC2BTransaction

def create_payment_tables():
    """Create payment tables using Django's schema editor"""
    
    style = no_style()
    sql = connection.ops.sql_table_creation_suffix()
    
    # Get the table creation SQL for each model
    with connection.schema_editor() as schema_editor:
        # Create PhonePayment table
        try:
            schema_editor.create_model(PhonePayment)
            print("✓ PhonePayment table created successfully")
        except Exception as e:
            print(f"PhonePayment table creation error: {e}")
        
        # Create MpesaB2CTransaction table
        try:
            schema_editor.create_model(MpesaB2CTransaction)
            print("✓ MpesaB2CTransaction table created successfully")
        except Exception as e:
            print(f"MpesaB2CTransaction table creation error: {e}")
        
        # Create MpesaC2BTransaction table
        try:
            schema_editor.create_model(MpesaC2BTransaction)
            print("✓ MpesaC2BTransaction table created successfully")
        except Exception as e:
            print(f"MpesaC2BTransaction table creation error: {e}")

def check_table_exists():
    """Check if tables exist"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments_phonepayment';")
        if cursor.fetchone():
            print("✓ payments_phonepayment table exists")
            return True
        else:
            print("✗ payments_phonepayment table does not exist")
            return False

if __name__ == "__main__":
    print("Checking table existence...")
    if not check_table_exists():
        print("\nCreating missing tables...")
        create_payment_tables()
        print("\nChecking again...")
        check_table_exists()
    else:
        print("Table already exists!")
