import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from users.serializers import UserSignupSerializer
from users.views import SignupView
from rest_framework.test import APIRequestFactory
from wallets.models import Wallet
from users.models import User as UserProfile

print("\n=== Testing Welcome Bonus ===\n")

try:
    # Create a test user
    factory = APIRequestFactory()
    data = {
        'email': 'welcometest@example.com',
        'password': 'testpass123',
        'username': 'welcometest',
        'full_name': 'Welcome Test'
    }

    request = factory.post('/api/v1/auth/signup/', data, format='json')
    view = SignupView.as_view()
    response = view(request)

    if response.status_code == 201:
        user_data = response.data.get('user', {})
        print(f"✓ User created: {user_data.get('username')}")
        
        # Check wallet points
        profile = UserProfile.objects.get(username='welcometest')
        wallet = Wallet.objects.get(user_id=profile)
        print(f"✓ Wallet created with {wallet.httn_points} HTTN Points")
        
        if wallet.httn_points == 100:
            print("\n✓✓✓ SUCCESS! Welcome bonus correctly applied! ✓✓✓\n")
        else:
            print(f"\n❌ FAILED: Expected 100 points, got {wallet.httn_points}\n")
    else:
        print(f"❌ Signup failed: {response.data}\n")
        
except Exception as e:
    print(f"❌ Error: {e}\n")
    import traceback
    traceback.print_exc()
