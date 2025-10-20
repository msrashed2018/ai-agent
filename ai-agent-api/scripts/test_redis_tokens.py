#!/usr/bin/env python3
"""
Test script to verify Redis token storage and authentication flow.

This script:
1. Logs in and gets tokens
2. Verifies tokens are stored in Redis
3. Tests /me endpoint with the token
4. Shows Redis token data
"""

import json
import sys
import redis
import requests

# Configuration
API_BASE_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
ADMIN_EMAIL = "admin@default.org"
ADMIN_PASSWORD = "admin123"


def main():
    print("=" * 60)
    print("🧪 Testing Redis Token Storage")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1️⃣  Logging in...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        response.raise_for_status()
        auth_data = response.json()
        print(f"   ✅ Login successful!")
        print(f"   User: {ADMIN_EMAIL}")
        print(f"   Token expires in: {auth_data['expires_in']} seconds")
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
        sys.exit(1)
    
    access_token = auth_data['access_token']
    refresh_token = auth_data['refresh_token']
    
    # Step 2: Check Redis
    print("\n2️⃣  Checking Redis for stored tokens...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        r.ping()
        
        # Get all token keys
        token_keys = r.keys('token:*')
        print(f"   ✅ Found {len(token_keys)} tokens in Redis")
        
        # Show recent tokens (last 3)
        for key in sorted(token_keys, reverse=True)[:3]:
            data = r.get(key)
            ttl = r.ttl(key)
            if data:
                token_data = json.loads(data)
                print(f"\n   📝 {key}")
                print(f"      User ID: {token_data.get('user_id')}")
                print(f"      Type: {token_data.get('token_type')}")
                print(f"      TTL: {ttl}s ({ttl/3600:.1f}h)")
                print(f"      Issued: {token_data.get('issued_at')}")
        
        # Check user tokens set
        user_tokens_keys = r.keys('user_tokens:*')
        print(f"\n   📊 User token sets: {len(user_tokens_keys)}")
        
    except Exception as e:
        print(f"   ❌ Redis check failed: {e}")
    
    # Step 3: Test /me endpoint
    print("\n3️⃣  Testing /me endpoint with access token...")
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        user_info = response.json()
        print(f"   ✅ Authentication successful!")
        print(f"   Email: {user_info['email']}")
        print(f"   Role: {user_info['role']}")
        print(f"   User ID: {user_info['id']}")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        if hasattr(e, 'response'):
            print(f"   Response: {e.response.text}")
    
    # Step 4: Test token revocation (logout)
    print("\n4️⃣  Testing token revocation (logout)...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        logout_data = response.json()
        print(f"   ✅ Logout successful!")
        print(f"   Tokens revoked: {logout_data.get('tokens_revoked', 0)}")
        
        # Verify token is now invalid
        print("\n   🔍 Verifying token is revoked...")
        response = requests.get(
            f"{API_BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if response.status_code == 401:
            print(f"   ✅ Token correctly rejected after logout!")
        else:
            print(f"   ⚠️  Token still works (unexpected)")
    except Exception as e:
        print(f"   ❌ Logout test failed: {e}")
    
    print("\n" + "=" * 60)
    print("✨ Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

