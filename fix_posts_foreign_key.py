#!/usr/bin/env python
"""
Fix posts table foreign key constraint to point to profiles instead of users
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.db import connection

def fix_posts_foreign_key():
    """Change posts.user_id foreign key from users to profiles"""
    
    print("="*60)
    print("🔧 FIXING POSTS TABLE FOREIGN KEY CONSTRAINT")
    print("="*60)
    
    with connection.cursor() as cursor:
        # Step 1: Check current constraints
        print("\n📋 Checking current constraints...")
        cursor.execute("""
            SELECT conname, confrelid::regclass 
            FROM pg_constraint 
            WHERE conrelid = 'posts'::regclass AND contype = 'f';
        """)
        constraints = cursor.fetchall()
        
        if constraints:
            for conname, ref_table in constraints:
                print(f"  Found constraint: {conname} -> {ref_table}")
        else:
            print("  No foreign key constraints found")
        
        # Step 2: Drop the existing constraint
        print("\n🗑️ Dropping old foreign key constraint...")
        cursor.execute("""
            ALTER TABLE posts DROP CONSTRAINT IF EXISTS posts_user_id_fkey;
        """)
        print("  ✅ Constraint dropped")
        
        # Step 3: Add new constraint to profiles
        print("\n🔗 Adding new foreign key constraint to profiles...")
        cursor.execute("""
            ALTER TABLE posts 
            ADD CONSTRAINT posts_user_id_fkey 
            FOREIGN KEY (user_id) REFERENCES profiles(id) ON DELETE CASCADE;
        """)
        print("  ✅ New constraint added")
        
        # Step 4: Verify the change
        print("\n✅ Verifying new constraint...")
        cursor.execute("""
            SELECT conname, confrelid::regclass 
            FROM pg_constraint 
            WHERE conrelid = 'posts'::regclass AND contype = 'f';
        """)
        new_constraints = cursor.fetchall()
        
        for conname, ref_table in new_constraints:
            print(f"  ✅ Active constraint: {conname} -> {ref_table}")
        
        # Step 5: Test with a sample post
        print("\n🧪 Testing post creation...")
        from django.contrib.auth.models import User
        from core.models import Profiles, Posts
        from django.utils import timezone
        import uuid
        
        try:
            user = User.objects.get(username='admin')
            profile = Profiles.objects.get(user_id=user.id)
            
            test_post = Posts.objects.create(
                content="Test post after fixing foreign key",
                user=profile,
                author_id=profile.id,
                is_sponsored=False,
                created_at=timezone.now(),
                likes_count=0,
                replies_count=0,
                reposts_count=0
            )
            print(f"  ✅ Test post created successfully! ID: {test_post.id}")
            test_post.delete()
            print("  ✅ Test post deleted")
            
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ FIX COMPLETE! Your posts should now work.")
    print("="*60)

if __name__ == "__main__":
    fix_posts_foreign_key()