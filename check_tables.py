import os
import django
import psycopg2
from psycopg2 import sql

# Set the DATABASE_URL
os.environ['DATABASE_URL'] = "postgresql://postgres.xxhnzlunpwmnxuhbwclg:7WaVbGfTTV7ZPwLM@aws-1-eu-north-1.pooler.supabase.com:6543/postgres"

django.setup()

from django.db import connection

# Check if tables exist
print("\n=== Checking Database Tables ===\n")

with connection.cursor() as cursor:
    # Get all tables in public schema
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = [
        'wallets_wallet',
        'posts_post',
        'users_user',
        'notifications_notification',
        'communities_community',
        'causes_cause',
        'auth_user',
    ]
    
    print(f"Total tables found: {len(tables)}\n")
    
    if tables:
        print("Tables in database:")
        for table in sorted(tables):
            status = "✓" if table in required_tables else " "
            print(f"  [{status}] {table}")
    else:
        print("⚠️  NO TABLES FOUND - Database is empty!")
    
    missing = [t for t in required_tables if t not in tables]
    if missing:
        print(f"\n❌ Missing tables: {missing}")
    else:
        print("\n✓ All required tables exist!")
