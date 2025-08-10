from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Create missing payment tables manually'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        # Create payments_phonepayment table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments_phonepayment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_type VARCHAR(20) NOT NULL,
                provider VARCHAR(20) NOT NULL DEFAULT 'mpesa',
                phone_number VARCHAR(15) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                description VARCHAR(255) NOT NULL,
                reference VARCHAR(100) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                transaction_id VARCHAR(255),
                receipt_number VARCHAR(255),
                created_at DATETIME NOT NULL,
                completed_at DATETIME,
                initiated_by_id INTEGER,
                mpesa_b2c_id INTEGER UNIQUE,
                mpesa_c2b_id INTEGER UNIQUE,
                FOREIGN KEY (initiated_by_id) REFERENCES auth_user (id) ON DELETE SET NULL,
                FOREIGN KEY (mpesa_b2c_id) REFERENCES payments_mpesab2ctransaction (id) ON DELETE SET NULL,
                FOREIGN KEY (mpesa_c2b_id) REFERENCES payments_mpesac2btransaction (id) ON DELETE SET NULL
            )
        """)
        
        # Create payments_mpesab2ctransaction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments_mpesab2ctransaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id VARCHAR(255),
                originator_conversation_id VARCHAR(255),
                phone_number VARCHAR(15) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                remarks VARCHAR(255),
                occasion VARCHAR(255),
                response_code VARCHAR(10),
                response_description TEXT,
                transaction_id VARCHAR(255),
                transaction_receipt VARCHAR(255),
                receiver_party_public_name VARCHAR(255),
                transaction_completed_date_time DATETIME,
                b2c_charges_paid_account_available_funds DECIMAL(10,2),
                b2c_utility_account_available_funds DECIMAL(10,2),
                b2c_working_account_available_funds DECIMAL(10,2),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                payment_id INTEGER,
                FOREIGN KEY (payment_id) REFERENCES payments_payment (id) ON DELETE CASCADE
            )
        """)
        
        # Create payments_mpesac2btransaction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments_mpesac2btransaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checkout_request_id VARCHAR(255) NOT NULL UNIQUE,
                merchant_request_id VARCHAR(255),
                phone_number VARCHAR(15) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                account_reference VARCHAR(255) NOT NULL,
                transaction_desc VARCHAR(255) NOT NULL,
                result_code VARCHAR(10),
                result_desc TEXT,
                mpesa_receipt_number VARCHAR(255),
                transaction_date DATETIME,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                payment_id INTEGER,
                FOREIGN KEY (payment_id) REFERENCES payments_payment (id) ON DELETE CASCADE
            )
        """)
        
        connection.commit()
        self.stdout.write(self.style.SUCCESS('Successfully created missing payment tables'))
