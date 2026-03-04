import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'herald_backend.settings')
django.setup()

from wallets.models import Wallet
from wallets.serializers import WalletSerializer
from users.models import User

print("Testing Wallet Serializer...")

# Get first user
user = User.objects.first()
if not user:
    print("No users found in database")
    exit(1)

print(f"User found: {user.username} (id: {user.id})")

# Get or create wallet
wallet, created = Wallet.objects.get_or_create(user_id=user)
print(f"Wallet {'created' if created else 'found'}: {wallet.id}")

# Test serialization
try:
    serializer = WalletSerializer(wallet)
    print("Serialization successful!")
    print("Data:", serializer.data)
except Exception as e:
    print(f"Serialization failed: {e}")
    import traceback
    traceback.print_exc()
