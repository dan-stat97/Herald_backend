import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.db import connection
from django.contrib.auth.models import User
from core.models import Profiles
import uuid
import traceback

print("🔧 FIXING PROFILES TABLE")
print("=" * 50)

# Step 1: Ensure profiles table has correct structure
with connection.cursor() as cursor:
    # Drop and recreate with correct types
    cursor.execute("DROP TABLE IF EXISTS profiles CASCADE;")
    print("✅ Dropped old profiles table")
    
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

# Step 2: Create profile for admin user
try:
    user = User.objects.get(username='admin')
    print(f"\n✅ Found admin user: {user.username} (ID: {user.id})")
    
    # Check if profile already exists
    existing = Profiles.objects.filter(user_id=user.id).first()
    if existing:
        print(f"⚠️ Profile already exists for user {user.id}")
    else:
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
        print(f"✅ Created profile for user {user.id}")
        
except User.DoesNotExist:
    print("\n❌ Admin user not found! Create one with:")
    print("   python manage.py createsuperuser")
    exit()
except Exception as e:
    print(f"\n❌ Error: {e}")
    traceback.print_exc()
    exit()

# Step 3: Verify
print("\n🔍 VERIFICATION")
print("-" * 30)

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM profiles;")
    count = cursor.fetchone()[0]
    print(f"Total profiles: {count}")
    
    if count > 0:
        cursor.execute("""
            SELECT p.id, p.user_id, p.username, u.username as auth_username
            FROM profiles p
            JOIN auth_user u ON p.user_id = u.id;
        """)
        profiles = cursor.fetchall()
        print("\n📋 Profile mappings:")
        for pid, user_id, prof_user, auth_user in profiles:
            print(f"   Profile {pid}: user_id={user_id} (profiles.username={prof_user}, auth.username={auth_user})")

print("\n" + "=" * 50)
print("✅ Setup complete! Try your API now.")