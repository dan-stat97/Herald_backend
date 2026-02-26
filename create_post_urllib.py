import urllib.request
import urllib.parse
import json
import ssl

# Disable SSL verification for local development
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Your token
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzcxODc2NjgwLCJpYXQiOjE3NzE3OTAyODAsImp0aSI6IjBiMjRhNDBkNWU5MTQxODg4MDExZjI4NjhmYzBiMDZjIiwidXNlcl9pZCI6IjEifQ.LAo-48nIv64Dkn07LPVijY7cDH4S2NspD8ZRPPbVoMU"

# Post data
post_data = {
    'content': 'Hello from the Herald API! This is my first post using urllib. 🎉'
}

# Convert to JSON and encode
data = json.dumps(post_data).encode('utf-8')

# Create request
url = "http://127.0.0.1:8000/api/posts/"
headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Content-Length': len(data)
}

req = urllib.request.Request(url, method='POST', headers=headers, data=data)

print("Creating a post...")

try:
    with urllib.request.urlopen(req, context=ssl_context) as response:
        response_data = response.read().decode('utf-8')
        post = json.loads(response_data)
        print(f"✅ Post created successfully! (Status: {response.status})")
        print(f"Post ID: {post['id']}")
        print(f"Content: {post['content']}")
        print(f"Created at: {post['created_at']}")
        
        # Save post ID for liking
        post_id = post['id']
        
        # Now like the post
        print(f"\nLiking post {post_id}...")
        like_url = f"http://127.0.0.1:8000/api/posts/{post_id}/like/"
        like_req = urllib.request.Request(like_url, method='POST', headers={'Authorization': f'Bearer {token}'})
        
        with urllib.request.urlopen(like_req, context=ssl_context) as like_response:
            like_data = like_response.read().decode('utf-8')
            print(f"✅ Like response: {json.loads(like_data)}")
            
except urllib.error.HTTPError as e:
    error_data = e.read().decode('utf-8') if e.read() else str(e)
    print(f"❌ HTTP Error: {e.code}")
    print(error_data)
except Exception as e:
    print(f"❌ Error: {e}")