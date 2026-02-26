import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.db import connection

def get_all_tables():
    """Get all tables in the database with details"""
    with connection.cursor() as cursor:
        # Get all tables with additional info
        cursor.execute("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = t.table_name) as column_count,
                obj_description(pg_class.oid) as table_description
            FROM information_schema.tables t
            LEFT JOIN pg_class ON pg_class.relname = t.table_name
            WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        print("=" * 80)
        print(f"📊 DATABASE TABLES REPORT")
        print("=" * 80)
        print(f"Total tables found: {len(tables)}")
        print("-" * 80)
        print(f"{'#':<4} {'Table Name':<30} {'Columns':<10} {'Rows':<15}")
        print("-" * 80)
        
        for idx, (table_name, column_count, description) in enumerate(tables, 1):
            # Get row count for each table
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                row_count = cursor.fetchone()[0]
            except:
                row_count = "Error"
            
            print(f"{idx:<4} {table_name:<30} {column_count:<10} {row_count:<15}")
            
            # Show first few columns for each table (optional)
            if idx <= 5:  # Show details for first 5 tables
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                    LIMIT 3;
                """, [table_name])
                columns = cursor.fetchall()
                if columns:
                    print(f"     First columns: {', '.join([f'{col[0]} ({col[1]})' for col in columns])}")
            print()
        
        return [table[0] for table in tables]

# Get all tables
tables = get_all_tables()

# Also check which tables are in your Django models
print("\n" + "=" * 80)
print("📋 DJANGO MODELS vs DATABASE TABLES")
print("=" * 80)

from django.apps import apps
django_tables = []
for model in apps.get_models():
    table_name = model._meta.db_table
    django_tables.append(table_name)
    in_db = "✅" if table_name in tables else "❌"
    print(f"{in_db} {table_name}")

print("\n" + "=" * 80)
print(f"Total Django models: {len(django_tables)}")
print(f"Total database tables: {len(tables)}")