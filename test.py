import psycopg2

# Connection pooling URL (port 6543 with pgbouncer)
DATABASE_URL = {
    'host': 'aws-1-eu-north-1.pooler.supabase.com',
    'port': '6543',
    'database': 'postgres',
    'user': 'postgres.xxhnzlunpwmnxuhbwclg',
    'password': '7WaVbGfTTV7ZPwLM',
    'sslmode': 'require'
}

print("Testing connection pooling (port 6543)...")
try:
    conn = psycopg2.connect(**DATABASE_URL)
    print("✅ SUCCESS! Connected via connection pooling!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")

# Direct connection (port 5432)
DIRECT_URL = {
    'host': 'aws-1-eu-north-1.pooler.supabase.com',
    'port': '5432',
    'database': 'postgres',
    'user': 'postgres.xxhnzlunpwmnxuhbwclg',
    'password': '72dZpep3hVZ4cOPD',
    'sslmode': 'require'
}

print("\nTesting direct connection (port 5432)...")
try:
    conn = psycopg2.connect(**DIRECT_URL)
    print("✅ SUCCESS! Connected via direct connection!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {e}")