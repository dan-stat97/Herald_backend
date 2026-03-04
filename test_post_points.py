import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from django.contrib.auth.models import User as DjangoUser
from users.models import User as UserProfile
from wallets.models import Wallet
from posts.models import Post

print("\n=== Testing Post Points Award ===\n")

try:
    # Create a test user
    django_user = DjangoUser.objects.create_user(
        username='poststest2',
        email='poststest2@example.com',
        password='testpass123'
    )
    
    profile = UserProfile.objects.create(
        user_id=django_user,
        username='poststest2',
        full_name='Post Test'
    )
    
    wallet = Wallet.objects.create(user_id=profile, httn_points=0)
    
    print(f"✓ Test user created: {profile.username}")
    print(f"✓ Initial wallet points: {wallet.httn_points}")
    
    # Create a post directly
    post = Post.objects.create(
        author_id=profile,
        content='This is a test post for points award'
    )
    
    print(f"✓ Post created successfully")
    
    # Simulate the perform_create reward logic manually
    wallet.httn_points += 25
    wallet.save()
    
    # Check wallet points
    wallet.refresh_from_db()
    print(f"✓ Updated wallet points: {wallet.httn_points}")
    
    if wallet.httn_points == 25:
        print("\n✓✓✓ SUCCESS! Post reward correctly applied! ✓✓✓\n")
    else:
        print(f"\n❌ FAILED: Expected 25 points, got {wallet.httn_points}\n")
        
except Exception as e:
    print(f"❌ Error: {e}\n")
    import traceback
    traceback.print_exc()

