import urllib.request
import urllib.parse
import json

# Your access token - replace with your actual token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxODc2NjgwLCJpYXQiOjE3NzE3OTAyODAsImp0aSI6IjBiMjRhNDBkNWU5MTQxODg4MDExZjI4NjhmYzBiMDZjIiwidXNlcl9pZCI6IjEifQ.LAo-48nIv64Dkn07LPVijY7cDH4S2NspD8ZRPPbVoMU"

# Create request
url = "http://127.0.0.1:8000/api/profiles/"
headers = {
    'Authorization': f'Bearer {token}'
}

req = urllib.request.Request(url, headers=headers)

try:
    # Send request
    with urllib.request.urlopen(req) as response:
        data = response.read()
        profiles = json.loads(data)
        print(f"✅ Success! Status code: {response.status}")
        print(f"Profiles: {profiles}")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode())
except Exception as e:
    print(f"❌ Error: {e}")