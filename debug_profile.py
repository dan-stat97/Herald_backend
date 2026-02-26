import urllib.request
import urllib.parse
import json
import ssl
import traceback

# Disable SSL verification for local development
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Your token
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
print(f"URL: {url}")
print(f"Token: {token[:30]}...")

try:
    with urllib.request.urlopen(req, context=ssl_context) as response:
        response_data = response.read().decode('utf-8')
        profile = json.loads(response_data)
        print(f"✅ Success! Status: {response.status}")
        print(json.dumps(profile, indent=2))
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code}")
    print(f"Reason: {e.reason}")
    
    # Read and print the error response from server
    error_data = e.read().decode('utf-8') if e.read() else "No error details"
    print(f"Server response: {error_data}")
    
    # Try to parse as JSON if possible
    try:
        error_json = json.loads(error_data)
        print(f"Error details: {json.dumps(error_json, indent=2)}")
    except:
        pass
        
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    traceback.print_exc()