#!/usr/bin/env python
import sqlite3
import os

def check_database():
    db_path = 'db.sqlite3'
    if not os.path.exists(db_path):
        print("Database file does not exist!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("All tables in database:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check specifically for payment tables
    payment_tables = [t[0] for t in tables if t[0].startswith('payments_')]
    print(f"\nPayment tables ({len(payment_tables)}):")
    for table in payment_tables:
        print(f"  - {table}")
    
    # Check if phonepayment table exists
    if 'payments_phonepayment' in [t[0] for t in tables]:
        print("\n✓ payments_phonepayment table exists")
        
        # Get table schema
        cursor.execute("PRAGMA table_info(payments_phonepayment);")
        columns = cursor.fetchall()
        print("Columns:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
    else:
        print("\n✗ payments_phonepayment table does NOT exist")
    
    conn.close()

if __name__ == "__main__":
    check_database()
