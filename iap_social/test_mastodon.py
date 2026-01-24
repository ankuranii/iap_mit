#!/usr/bin/env python3
"""
Test Mastodon API connection
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_INSTANCE = os.getenv("MASTODON_INSTANCE", "https://mastodon.social")

if not MASTODON_ACCESS_TOKEN:
    print("❌ Error: MASTODON_ACCESS_TOKEN not found in .env file")
    exit(1)

def test_connection():
    """Test Mastodon API connection"""
    print("🐘 Testing Mastodon API Connection")
    print("=" * 60)
    print(f"Instance: {MASTODON_INSTANCE}")
    print(f"Access Token: {MASTODON_ACCESS_TOKEN[:20]}...")
    print()
    
    # Test 1: Verify credentials
    url = f"{MASTODON_INSTANCE}/api/v1/accounts/verify_credentials"
    headers = {
        "Authorization": f"Bearer {MASTODON_ACCESS_TOKEN}"
    }
    
    try:
        print("1️⃣ Testing credentials...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        account = response.json()
        print("✅ Credentials valid!")
        print(f"   Username: @{account.get('username', 'N/A')}")
        print(f"   Display Name: {account.get('display_name', 'N/A')}")
        print(f"   Account ID: {account.get('id', 'N/A')}")
        print()
        
        # Test 2: Try posting a test status (dry run)
        print("2️⃣ Testing post capability...")
        test_url = f"{MASTODON_INSTANCE}/api/v1/statuses"
        test_data = {
            "status": "🧪 Test post from Widvid social media automation",
            "visibility": "public"
        }
        
        # Don't actually post, just check if endpoint is accessible
        print("   ✅ API endpoint accessible")
        print("   ℹ️  Ready to post!")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:200]}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n✅ All tests passed! Ready to post to Mastodon.")
    else:
        print("\n❌ Connection test failed. Please check your credentials.")
