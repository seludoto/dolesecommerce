#!/usr/bin/env python
import sqlite3
import os

def create_phonepayment_table():
    db_path = 'db.sqlite3'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop table if it exists (to avoid conflicts)
    cursor.execute("DROP TABLE IF EXISTS payments_phonepayment;")
    
    # Create the PhonePayment table
    create_sql = '''
    CREATE TABLE payments_phonepayment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_type VARCHAR(20) NOT NULL,
        provider VARCHAR(20) NOT NULL DEFAULT 'mpesa',
        phone_number VARCHAR(15) NOT NULL,
        amount DECIMAL(10,2) NOT NULL,
        description VARCHAR(255) NOT NULL,
        reference VARCHAR(100) NOT NULL UNIQUE,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        transaction_id VARCHAR(255) NOT NULL DEFAULT '',
        receipt_number VARCHAR(255) NOT NULL DEFAULT '',
        created_at DATETIME NOT NULL,
        completed_at DATETIME NULL,
        initiated_by_id INTEGER NULL,
        mpesa_b2c_id INTEGER NULL UNIQUE,
        mpesa_c2b_id INTEGER NULL UNIQUE,
        FOREIGN KEY (initiated_by_id) REFERENCES auth_user (id),
        FOREIGN KEY (mpesa_b2c_id) REFERENCES payments_mpesab2ctransaction (id),
        FOREIGN KEY (mpesa_c2b_id) REFERENCES payments_mpesac2btransaction (id)
    );
    '''
    
    try:
        cursor.execute(create_sql)
        conn.commit()
        print("✓ payments_phonepayment table created successfully")
        
        # Verify the table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments_phonepayment';")
        if cursor.fetchone():
            print("✓ Table creation verified")
        else:
            print("✗ Table creation failed")
            
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_phonepayment_table()
