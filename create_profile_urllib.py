import urllib.request
import urllib.parse
import json
import ssl

# Disable SSL verification for local development
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Your token from quick_test.py
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxODc2NjgwLCJpYXQiOjE3NzE3OTAyODAsImp0aSI6IjBiMjRhNDBkNWU5MTQxODg4MDExZjI4NjhmYzBiMDZjIiwidXNlcl9pZCI6IjEifQ.LAo-48nIv64Dkn07LPVijY7cDH4S2NspD8ZRPPbVoMU"

# Create profile from current user
url = "http://127.0.0.1:8000/api/profiles/create_from_user/"
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Create request
req = urllib.request.Request(url, method='POST', headers=headers)

print("Creating profile from current user...")

try:
    with urllib.request.urlopen(req, context=ssl_context) as response:
        response_data = response.read().decode('utf-8')
        profile = json.loads(response_data)
        print(f"✅ Profile created successfully! (Status: {response.status})")
        print(json.dumps(profile, indent=2))
except urllib.error.HTTPError as e:
    error_data = e.read().decode('utf-8') if e.read() else str(e)
    print(f"❌ HTTP Error: {e.code}")
    if e.code == 400:
        print("⚠️ Profile might already exist:")
        print(error_data)
    else:
        print(error_data)
except Exception as e:
    print(f"❌ Error: {e}")