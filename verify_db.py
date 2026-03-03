#!/usr/bin/env python
"""
Verify database tables exist on production.
Run this after deployment to check if migrations were applied.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.db import connection

def verify_database():
    """Check if all required tables exist."""
    required_tables = [
        'wallets_wallet',
        'users_user', 
        'posts_post',
        'auth_user',
        'notifications_notification',
        'communities_community',
        'causes_cause'
    ]
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
    
    print("\n=== Database Verification ===\n")
    print(f"Total tables found: {len(existing_tables)}\n")
    
    missing_tables = []
    for table in required_tables:
        if table in existing_tables:
            print(f"✓ {table}")
        else:
            print(f"✗ {table} (MISSING)")
            missing_tables.append(table)
    
    if missing_tables:
        print(f"\n❌ Missing {len(missing_tables)} required tables!")
        print("Run: python manage.py migrate")
        sys.exit(1)
    else:
        print("\n✓ All required tables exist!")
        sys.exit(0)

if __name__ == '__main__':
    verify_database()
