
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from core.models import Profiles
import uuid
import traceback

print("🔧 FINAL FIX - PROFILES TABLE")
print("=" * 50)

# Check model field types
print("\n📋 Checking Profiles model fields:")
from core.models import Profiles
for field in Profiles._meta.get_fields():
    field_type = field.__class__.__name__
    print(f"  {field.name}: {field_type}")
    if field.name == 'user_id' and field_type != 'IntegerField':
        print(f"  ⚠️  WARNING: user_id should be IntegerField, but is {field_type}!")
        print("  Please update core/models.py and restart Django shell")

# Recreate table with correct structure
with connection.cursor() as cursor:
    cursor.execute("DROP TABLE IF EXISTS profiles CASCADE;")
    print("\n✅ Dropped old profiles table")
    
    cursor.execute("""
    CREATE TABLE profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id INTEGER NOT NULL,
        username VARCHAR(50) UNIQUE NOT NULL,
        full_name VARCHAR(100),
        display_name TEXT,
        verified BOOLEAN DEFAULT FALSE,
        pro_status BOOLEAN DEFAULT FALSE,
        balance DECIMAL DEFAULT 0,
        avatar_url TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """)
    print("✅ Created new profiles table with INTEGER user_id")
    
    cursor.execute("CREATE INDEX idx_profiles_user_id ON profiles(user_id);")
    print("✅ Created index")

# Create profile for admin user
try:
    user = User.objects.get(username='admin')
    print(f"\n✅ Found admin user: {user.username} (ID: {user.id})")
    
    profile = Profiles.objects.create(
        id=uuid.uuid4(),
        user_id=user.id,
        username=user.username,
        full_name='Admin User',
        display_name='admin',
        verified=True,
        pro_status=True,
        balance=1000.00
    )
    print(f"✅ Profile created for user {user.id}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()

# Final verification
print("\n🔍 FINAL VERIFICATION")
print("-" * 30)

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM profiles;")
    count = cursor.fetchone()[0]
    print(f"Total profiles: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT p.id, p.user_id, p.username, u.username 
            FROM profiles p
            JOIN auth_user u ON p.user_id = u.id;
        """)
        rows = cursor.fetchall()
        for pid, uid, p_username, u_username in rows:
            print(f"✅ Profile {pid}: user_id={uid} -> auth_user.{u_username}")

print("\n" + "=" * 50)
print("Setup complete! Try your API now.")