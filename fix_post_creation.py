# debug_post_creation.py
import os
import django
import json
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import Profiles, Posts
from django.db import connection
from django.utils import timezone
import uuid

def debug_post_creation():
    """Diagnose post creation issues"""
    
    print("="*60)
    print("🔍 POST CREATION DIAGNOSTIC TOOL")
    print("="*60)
    
    # Step 1: Check database connection
    print("\n📡 Checking database connection...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Database connection OK")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Step 2: Check admin user
    print("\n👤 Checking admin user...")
    try:
        user = User.objects.get(username='admin')
        print(f"✅ Admin user found: ID={user.id}, username={user.username}")
    except User.DoesNotExist:
        print("❌ Admin user not found!")
        return
    
    # Step 3: Check admin profile
    print("\n📋 Checking admin profile...")
    try:
        profile = Profiles.objects.get(user_id=user.id)
        print(f"✅ Profile found: ID={profile.id}, username={profile.username}")
        print(f"   Profile details:")
        print(f"     - user_id: {profile.user_id} (type: {type(profile.user_id).__name__})")
        print(f"     - id: {profile.id} (type: {type(profile.id).__name__})")
        print(f"     - username: {profile.username}")
        print(f"     - verified: {profile.verified}")
    except Profiles.DoesNotExist:
        print("❌ Profile not found for admin user!")
        return
    
    # Step 4: Check posts table structure
    print("\n📊 Checking posts table structure...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'posts'
            ORDER BY ordinal_position;
        """)
        columns = cursor.fetchall()
        print(f"Posts table has {len(columns)} columns:")
        required_fields = []
        for col in columns:
            name, dtype, nullable = col
            is_required = nullable == 'NO' and name not in ['id', 'created_at']
            if is_required:
                required_fields.append(name)
            status = "🔴 REQUIRED" if is_required else "🟢 OPTIONAL"
            print(f"  {status} - {name}: {dtype}")
        
        if required_fields:
            print(f"\n⚠️ Required fields: {', '.join(required_fields)}")
    
    # Step 5: Check foreign key constraints
    print("\n🔗 Checking foreign key constraints...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT conname, conrelid::regclass, confrelid::regclass
            FROM pg_constraint
            WHERE conrelid = 'posts'::regclass AND contype = 'f';
        """)
        constraints = cursor.fetchall()
        for conname, table, ref_table in constraints:
            print(f"  {conname}: {table}.??? -> {ref_table}")
    
    # Step 6: Try to create a post with different approaches
    print("\n🧪 Attempting to create a post...")
    
    # Approach 1: Direct SQL
    print("\n  Approach 1: Direct SQL")
    with connection.cursor() as cursor:
        try:
            post_id = uuid.uuid4()
            cursor.execute("""
                INSERT INTO posts (id, user_id, author_id, content, is_sponsored, created_at, likes_count, replies_count, reposts_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, [
                str(post_id),
                str(profile.id),
                str(profile.id),
                f"Test post at {timezone.now()}",
                False,
                timezone.now(),
                0, 0, 0
            ])
            result = cursor.fetchone()
            print(f"  ✅ SQL INSERT succeeded! Post ID: {result[0]}")
            
            # Clean up
            cursor.execute("DELETE FROM posts WHERE id = %s", [str(post_id)])
            print("  ✅ Test post cleaned up")
        except Exception as e:
            print(f"  ❌ SQL INSERT failed: {e}")
            print(f"     Error type: {type(e).__name__}")
            if hasattr(e, 'diag') and e.diag:
                print(f"     Detail: {e.diag.message_detail}")
    
    # Approach 2: Django ORM minimal
    print("\n  Approach 2: Django ORM (minimal fields)")
    try:
        post = Posts.objects.create(
            content=f"ORM test at {timezone.now()}",
            user=profile,
        )
        print(f"  ✅ ORM minimal succeeded! Post ID: {post.id}")
        post.delete()
        print("  ✅ Test post cleaned up")
    except Exception as e:
        print(f"  ❌ ORM minimal failed: {e}")
        traceback.print_exc()
    
    # Approach 3: Django ORM with all fields
    print("\n  Approach 3: Django ORM (all fields)")
    try:
        post = Posts.objects.create(
            content=f"ORM test at {timezone.now()}",
            user=profile,
            author_id=profile.id,
            is_sponsored=False,
            created_at=timezone.now(),
            likes_count=0,
            replies_count=0,
            reposts_count=0
        )
        print(f"  ✅ ORM all fields succeeded! Post ID: {post.id}")
        post.delete()
        print("  ✅ Test post cleaned up")
    except Exception as e:
        print(f"  ❌ ORM all fields failed: {e}")
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Diagnostic complete. Check the results above.")
    print("="*60)

if __name__ == "__main__":
    debug_post_creation()