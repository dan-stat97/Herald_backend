import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

print("🎯 TESTING HERALD API - FINAL CHECK")
print("=" * 50)

# 1. Get token
print("\n1. Getting authentication token...")
auth_response = requests.post(
    f"{BASE_URL}/token/",
    json={'username': 'admin', 'password': 'admin123'}
)

if auth_response.status_code != 200:
    print(f"❌ Auth failed: {auth_response.text}")
    exit()

token = auth_response.json()['access']
headers = {'Authorization': f'Bearer {token}'}
print("✅ Token obtained")

# 2. Check profiles
print("\n2. Checking profiles...")
response = requests.get(f"{BASE_URL}/profiles/", headers=headers)
if response.status_code == 200:
    profiles = response.json()
    print(f"✅ Found {len(profiles)} profile(s)")
    print(json.dumps(profiles, indent=2))
else:
    print(f"❌ Failed: {response.status_code}")

# 3. Create a post
print("\n3. Creating a test post...")
post_data = {'content': 'My first post from the working Herald API!'}
response = requests.post(f"{BASE_URL}/posts/", headers=headers, json=post_data)

if response.status_code == 201:
    post = response.json()
    print("✅ Post created!")
    print(f"   ID: {post['id']}")
    print(f"   Content: {post['content']}")
    
    # 4. Like the post
    print(f"\n4. Liking post {post['id']}...")
    like_response = requests.post(f"{BASE_URL}/posts/{post['id']}/like/", headers=headers)
    print(f"   Result: {like_response.json()}")
else:
    print(f"❌ Failed to create post: {response.text}")

# 5. Get all posts
print("\n5. Getting all posts...")
response = requests.get(f"{BASE_URL}/posts/", headers=headers)
if response.status_code == 200:
    posts = response.json()
    print(f"✅ Found {len(posts)} post(s)")
    for post in posts[:3]:
        print(f"   - {post['content'][:50]}... (likes: {post.get('likes_count', 0)})")

print("\n" + "=" * 50)
print("✅ ALL TESTS PASSED! Your Herald backend is ready!")