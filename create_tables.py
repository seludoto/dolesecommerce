#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dolesecommerce.settings')
django.setup()

from django.db import connection

def create_missing_tables():
    with connection.cursor() as cursor:
        # Create PhonePayment table
        sql = '''
        CREATE TABLE IF NOT EXISTS "payments_phonepayment" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "payment_type" varchar(20) NOT NULL,
            "provider" varchar(20) NOT NULL,
            "phone_number" varchar(15) NOT NULL,
            "amount" decimal NOT NULL,
            "description" varchar(255) NOT NULL,
            "reference" varchar(100) NOT NULL UNIQUE,
            "status" varchar(20) NOT NULL,
            "transaction_id" varchar(255) NOT NULL,
            "receipt_number" varchar(255) NOT NULL,
            "created_at" datetime NOT NULL,
            "completed_at" datetime NULL,
            "initiated_by_id" integer NULL,
            "mpesa_b2c_id" integer NULL UNIQUE,
            "mpesa_c2b_id" integer NULL UNIQUE
        )
        '''
        cursor.execute(sql)
        print("PhonePayment table created successfully")

        # Create MpesaB2CTransaction table  
        sql_b2c = '''
        CREATE TABLE IF NOT EXISTS "payments_mpesab2ctransaction" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "conversation_id" varchar(255) NOT NULL UNIQUE,
            "originator_conversation_id" varchar(255) NOT NULL,
            "phone_number" varchar(15) NOT NULL,
            "amount" decimal NOT NULL,
            "remarks" varchar(255) NOT NULL,
            "occasion" varchar(100) NOT NULL,
            "status" varchar(20) NOT NULL,
            "response_code" varchar(10) NOT NULL,
            "response_description" text NOT NULL,
            "transaction_id" varchar(255) NOT NULL,
            "transaction_receipt" varchar(255) NOT NULL,
            "b2c_charges_paid_account_available_funds" decimal NULL,
            "receiver_party_public_name" varchar(255) NOT NULL,
            "transaction_completed_date_time" datetime NULL,
            "b2c_utility_account_available_funds" decimal NULL,
            "b2c_working_account_available_funds" decimal NULL,
            "created_at" datetime NOT NULL,
            "updated_at" datetime NOT NULL,
            "payment_id" integer NULL
        )
        '''
        cursor.execute(sql_b2c)
        print("MpesaB2CTransaction table created successfully")

        # Create MpesaC2BTransaction table
        sql_c2b = '''
        CREATE TABLE IF NOT EXISTS "payments_mpesac2btransaction" (
            "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
            "checkout_request_id" varchar(255) NOT NULL UNIQUE,
            "merchant_request_id" varchar(255) NOT NULL,
            "phone_number" varchar(15) NOT NULL,
            "amount" decimal NOT NULL,
            "account_reference" varchar(255) NOT NULL,
            "transaction_desc" varchar(255) NOT NULL,
            "status" varchar(20) NOT NULL,
            "result_code" varchar(10) NOT NULL,
            "result_desc" text NOT NULL,
            "mpesa_receipt_number" varchar(255) NOT NULL,
            "transaction_date" datetime NULL,
            "created_at" datetime NOT NULL,
            "updated_at" datetime NOT NULL,
            "payment_id" integer NOT NULL
        )
        '''
        cursor.execute(sql_c2b)
        print("MpesaC2BTransaction table created successfully")

if __name__ == "__main__":
    try:
        create_missing_tables()
        print("All tables created successfully!")
    except Exception as e:
        print(f"Error: {e}")
