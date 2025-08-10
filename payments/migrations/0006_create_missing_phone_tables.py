# Manual migration to fix missing phone payment tables
from django.db import migrations


def create_missing_tables(apps, schema_editor):
    """Create missing payment tables using raw SQL"""
    from django.db import connection
    
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
                "initiated_by_id" bigint NULL,
                "mpesa_b2c_id" bigint NULL UNIQUE,
                "mpesa_c2b_id" bigint NULL UNIQUE
            )
        ''')


def reverse_create_tables(apps, schema_editor):
    """Drop the tables if needed"""
    from django.db import connection
    
    with connection.cursor() as cursor:
        cursor.execute('DROP TABLE IF EXISTS "payments_phonepayment"')


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_auto_20250808_1748'),
    ]

    operations = [
        migrations.RunPython(create_missing_tables, reverse_create_tables),
    ]
