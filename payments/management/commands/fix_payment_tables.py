from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Create missing payment tables manually'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create PhonePayment table
            cursor.execute('''
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
                    "initiated_by_id" bigint NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "mpesa_b2c_id" bigint NULL UNIQUE REFERENCES "payments_mpesab2ctransaction" ("id") DEFERRABLE INITIALLY DEFERRED,
                    "mpesa_c2b_id" bigint NULL UNIQUE REFERENCES "payments_mpesac2btransaction" ("id") DEFERRABLE INITIALLY DEFERRED
                )
            ''')

            # Create MpesaB2CTransaction table
            cursor.execute('''
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
                    "payment_id" bigint NULL REFERENCES "payments_payment" ("id") DEFERRABLE INITIALLY DEFERRED
                )
            ''')

            # Create MpesaC2BTransaction table
            cursor.execute('''
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
                    "payment_id" bigint NOT NULL REFERENCES "payments_payment" ("id") DEFERRABLE INITIALLY DEFERRED
                )
            ''')

            self.stdout.write(
                self.style.SUCCESS('Successfully created missing payment tables')
            )
