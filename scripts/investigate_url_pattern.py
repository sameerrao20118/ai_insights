#!/usr/bin/env python3
"""
Enterprise Gateway URL Structure Investigator
This will help determine the correct URL format for your gateway.
"""
import requests
from config.settings import settings
from auth import get_cached_or_new_token

print("=" * 80)
print("ENTERPRISE GATEWAY URL STRUCTURE INVESTIGATOR")
print("=" * 80)

token = get_cached_or_new_token()
print(f"✅ Token obtained")

print(f"\nCurrent settings:")
print(f"  LLM_API_BASE: {settings.llm_api_base}")
print(f"  LLM_DEPLOYMENT_NAME: {settings.llm_deployment_name}")

# Let's try different URL patterns
test_payloads = {
    "messages": [
        {"role": "user", "content": "Hi"}
    ],
    "temperature": 0.2,
    "max_tokens": 10
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

print("\n" + "=" * 80)
print("TESTING DIFFERENT URL PATTERNS")
print("=" * 80)

# Pattern 1: Use LLM_API_BASE as-is (already complete endpoint)
print("\n📌 TEST 1: Using LLM_API_BASE as complete endpoint")
url1 = settings.llm_api_base
print(f"   URL: {url1}")
try:
    resp = requests.post(url1, headers=headers, json=test_payloads, verify=False, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {resp.json()}")
    else:
        print(f"   ❌ Failed: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Pattern 2: Remove deployment from base, use it separately
print("\n📌 TEST 2: Base URL without deployment, add /chat/completions")
# Extract base without deployment
base_parts = settings.llm_api_base.split('/genai/openai/')
if len(base_parts) == 2:
    url2 = f"{base_parts[0]}/genai/openai/chat/completions"
    print(f"   URL: {url2}")
    # Add model to payload
    test_payloads2 = {**test_payloads, "model": settings.llm_deployment_name}
    try:
        resp = requests.post(url2, headers=headers, json=test_payloads2, verify=False, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"   ✅ SUCCESS!")
            print(f"   Response: {resp.json()}")
        else:
            print(f"   ❌ Failed: {resp.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

# Pattern 3: OpenAI-style with model in payload
print("\n📌 TEST 3: Using deployment in model field of payload")
url3 = f"{base_parts[0]}/genai/openai/v1/chat/completions"
print(f"   URL: {url3}")
test_payloads3 = {**test_payloads, "model": settings.llm_deployment_name}
try:
    resp = requests.post(url3, headers=headers, json=test_payloads3, verify=False, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {resp.json()}")
    else:
        print(f"   ❌ Failed: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Pattern 4: Check if there's /v1 suffix needed
print("\n📌 TEST 4: LLM_API_BASE + /v1/chat/completions")
url4 = f"{settings.llm_api_base.rstrip('/')}/v1/chat/completions"
print(f"   URL: {url4}")
try:
    resp = requests.post(url4, headers=headers, json=test_payloads, verify=False, timeout=10)
    print(f"   Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"   ✅ SUCCESS!")
        print(f"   Response: {resp.json()}")
    else:
        print(f"   ❌ Failed: {resp.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
print("\n💡 The pattern that returns Status 200 is the correct one!")
print("   Update your .env accordingly based on the successful pattern.")
