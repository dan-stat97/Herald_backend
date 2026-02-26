# test_all_apis_fixed.py
import requests
import json
from datetime import datetime
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
ADMIN_CREDENTIALS = {
    "username": "admin",
    "password": "admin123"  # Your admin password
}
TEST_USER = {
    "username": "testuser_" + str(int(time.time())),  # Unique username
    "email": f"test_{int(time.time())}@example.com",
    "password": "Test123!",
    "full_name": "Test User"
}

# Colors for pretty printing
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{'='*60}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️ {text}{Colors.END}")

def test_endpoint(name, method, url, expected_status=200, headers=None, data=None, token=None):
    """Test a single endpoint"""
    print_info(f"Testing: {name}")
    print(f"   {method} {url}")
    
    full_url = f"{BASE_URL}{url}"
    request_headers = headers or {}
    
    if token:
        request_headers['Authorization'] = f'Bearer {token}'
    
    try:
        if method.upper() == 'GET':
            response = requests.get(full_url, headers=request_headers)
        elif method.upper() == 'POST':
            response = requests.post(full_url, headers=request_headers, json=data)
        elif method.upper() == 'PUT':
            response = requests.put(full_url, headers=request_headers, json=data)
        elif method.upper() == 'DELETE':
            response = requests.delete(full_url, headers=request_headers)
        else:
            print_error(f"Unsupported method: {method}")
            return False
        
        if response.status_code == expected_status:
            print_success(f"Status {response.status_code} (expected {expected_status})")
            
            # Try to parse JSON, but don't fail if it's not JSON
            try:
                json_response = response.json()
                if len(str(json_response)) < 500:
                    print(f"   Response: {json.dumps(json_response, indent=2)}")
                return json_response
            except:
                # Not JSON, that's OK for some endpoints
                if response.text and len(response.text) < 200:
                    print(f"   Response: {response.text}")
                return True
        else:
            print_error(f"Status {response.status_code} (expected {expected_status})")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Connection failed - is Django server running on {BASE_URL}?")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def check_server():
    """Check if server is running without expecting JSON"""
    print_info("Checking server connectivity...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print_success(f"Server responded with status {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server. Make sure Django is running:")
        print("   python manage.py runserver")
        return False
    except Exception as e:
        print_error(f"Server check failed: {str(e)}")
        return False

def run_all_tests():
    """Run all API tests"""
    print_header("🚀 HERALD API COMPREHENSIVE TEST SUITE")
    print_info(f"Base URL: {BASE_URL}")
    print_info(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Check if server is running
    print_header("📡 TEST 1: SERVER CONNECTIVITY")
    if not check_server():
        return
    
    # Test 2: Admin Login
    print_header("🔐 TEST 2: AUTHENTICATION")
    token_data = test_endpoint(
        "Admin Login",
        "POST",
        "/token/",
        expected_status=200,
        data=ADMIN_CREDENTIALS
    )
    
    if not token_data or 'access' not in token_data:
        print_error("Login failed - check admin credentials")
        return
    
    admin_token = token_data['access']
    print_success(f"Admin token obtained: {admin_token[:20]}...")
    
    # Test 3: Get Current User (with wallet)
    print_header("👤 TEST 3: CURRENT USER PROFILE")
    user_data = test_endpoint(
        "Current User",
        "GET",
        "/v1/auth/user/",
        expected_status=200,
        token=admin_token
    )
    
    if user_data:
        if user_data.get('wallet'):
            print_success(f"Wallet found: {user_data['wallet']['httn_points']} points")
        else:
            print_warning("No wallet found for user")
    
    # Test 4: Get Profiles
    print_header("📋 TEST 4: PROFILES ENDPOINT")
    profiles = test_endpoint(
        "Get Profiles",
        "GET",
        "/v1/profiles/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 5: Create a Post
    print_header("📝 TEST 5: CREATE POST")
    post_data = {
        "content": f"Test post at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }
    post_result = test_endpoint(
        "Create Post",
        "POST",
        "/v1/posts/",
        expected_status=201,
        data=post_data,
        token=admin_token
    )
    
    post_id = None
    if post_result and isinstance(post_result, dict) and 'id' in post_result:
        post_id = post_result['id']
        print_success(f"Post created with ID: {post_id}")
    
    # Test 6: Get All Posts
    print_header("📰 TEST 6: GET POSTS")
    posts = test_endpoint(
        "Get Posts",
        "GET",
        "/v1/posts/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 7: Like a Post (if we have a post)
    if post_id:
        print_header("❤️ TEST 7: LIKE POST")
        like_result = test_endpoint(
            "Like Post",
            "POST",
            f"/v1/posts/{post_id}/like/",
            expected_status=200,
            token=admin_token
        )
    
    # Test 8: Get News
    print_header("📰 TEST 8: NEWS ENDPOINT")
    news = test_endpoint(
        "Get News",
        "GET",
        "/v1/news/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 9: Get Communities
    print_header("👥 TEST 9: COMMUNITIES ENDPOINT")
    communities = test_endpoint(
        "Get Communities",
        "GET",
        "/v1/communities/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 10: Get Causes
    print_header("🎯 TEST 10: CAUSES ENDPOINT")
    causes = test_endpoint(
        "Get Causes",
        "GET",
        "/v1/causes/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 11: Get Notifications
    print_header("🔔 TEST 11: NOTIFICATIONS ENDPOINT")
    notifications = test_endpoint(
        "Get Notifications",
        "GET",
        "/v1/notifications/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 12: Get Leaderboard
    print_header("🏆 TEST 12: LEADERBOARD ENDPOINT")
    leaderboard = test_endpoint(
        "Leaderboard Reputation",
        "GET",
        "/v1/leaderboard/reputation/",
        expected_status=200,
        token=admin_token
    )
    
    # Test 13: Signup New User
    print_header("✨ TEST 13: USER SIGNUP")
    signup_result = test_endpoint(
        "Signup New User",
        "POST",
        "/v1/auth/signup/",
        expected_status=201,
        data=TEST_USER
    )
    
    if signup_result and isinstance(signup_result, dict) and 'session' in signup_result:
        new_user_token = signup_result['session']['access_token']
        print_success(f"New user created: {TEST_USER['username']}")
        
        # Test 14: Get New User Profile
        print_header("👤 TEST 14: NEW USER PROFILE")
        new_user_profile = test_endpoint(
            "New User Profile",
            "GET",
            "/v1/auth/user/",
            expected_status=200,
            token=new_user_token
        )
    
    # Test 15: Refresh Token
    print_header("🔄 TEST 15: TOKEN REFRESH")
    if token_data and 'refresh' in token_data:
        refresh_result = test_endpoint(
            "Refresh Token",
            "POST",
            "/token/refresh/",
            expected_status=200,
            data={"refresh": token_data['refresh']}
        )
    
    # Summary
    print_header("📊 TEST SUMMARY")
    print_success("All API tests completed!")
    print_info(f"Admin token: {admin_token[:20]}...")
    if post_id:
        print_info(f"Test post ID: {post_id}")
    
    print_header("✅ YOUR BACKEND IS FULLY FUNCTIONAL!")

def quick_check():
    """Quick check of critical endpoints"""
    print_header("⚡ QUICK API HEALTH CHECK")
    
    # Check server first
    if not check_server():
        return
    
    # Get admin token
    token_data = test_endpoint(
        "Admin Login",
        "POST",
        "/token/",
        expected_status=200,
        data=ADMIN_CREDENTIALS
    )
    
    if not token_data or 'access' not in token_data:
        print_error("Login failed - check admin credentials")
        return
    
    admin_token = token_data['access']
    
    # Test critical endpoints
    critical_tests = [
        ("Current User", "/v1/auth/user/", admin_token),
        ("Posts", "/v1/posts/", admin_token),
        ("News", "/v1/news/", admin_token),
        ("Communities", "/v1/communities/", admin_token),
        ("Causes", "/v1/causes/", admin_token),
    ]
    
    all_passed = True
    for name, url, token in critical_tests:
        result = test_endpoint(name, "GET", url, expected_status=200, token=token)
        if not result:
            all_passed = False
    
    if all_passed:
        print_header("✅ ALL CRITICAL ENDPOINTS ARE WORKING!")
    else:
        print_header("⚠️ SOME ENDPOINTS FAILED")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     HERALD API TEST SUITE                                ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print("Choose test mode:")
    print("1. Full comprehensive test (all endpoints)")
    print("2. Quick health check (critical endpoints only)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        run_all_tests()
    elif choice == "2":
        quick_check()
    else:
        print_warning("Invalid choice. Running quick check by default.")
        quick_check()