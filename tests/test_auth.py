#!/usr/bin/env python3
"""
Test script to verify enterprise authentication is working.
Run this on your enterprise machine to debug auth issues.
"""
from config.settings import settings
from auth import get_cached_or_new_token

print("=" * 60)
print("ENTERPRISE AUTHENTICATION TEST")
print("=" * 60)

print(f"\n📋 Configuration:")
print(f"   SERVICE_ACCOUNT: {settings.service_account}")
print(f"   AUTH_URL: {settings.auth_url}")
print(f"   LLM_PROVIDER: {settings.llm_provider}")

print(f"\n🔑 Testing authentication...")
try:
    token = get_cached_or_new_token()
    print(f"   ✅ SUCCESS! Token obtained: {token[:50]}...")
    print(f"   Token length: {len(token)} characters")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print("\n📜 Full traceback:")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
