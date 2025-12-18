#!/usr/bin/env python3
"""
Comprehensive debugging script for enterprise LLM connection issues.
This will test each component and show exactly where the failure occurs.
"""
import sys
import traceback
from config.settings import settings
from auth import get_cached_or_new_token

print("=" * 80)
print("COMPREHENSIVE LLM CONNECTION DEBUGGER")
print("=" * 80)

# ============================================================================
# STEP 1: Configuration Check
# ============================================================================
print("\n📋 STEP 1: Configuration Check")
print("-" * 80)
print(f"LLM_PROVIDER: {settings.llm_provider}")
print(f"LLM_API_BASE: {settings.llm_api_base}")
print(f"LLM_DEPLOYMENT_NAME: {settings.llm_deployment_name}")
print(f"LLM_API_VERSION: {settings.llm_api_version}")
print(f"EMBEDDING_API_BASE: {settings.embedding_api_base}")
print(f"EMBEDDING_DEPLOYMENT_NAME: {settings.embedding_deployment_name}")

if settings.llm_provider.lower() == "ollama":
    print("\n⚠️  WARNING: LLM_PROVIDER is set to 'ollama'")
    print("   For enterprise mode, it should be 'enterprise' or similar")
    print("   The app will try to connect to localhost instead of enterprise gateway!")

# ============================================================================
# STEP 2: Authentication Test
# ============================================================================
print("\n🔑 STEP 2: Authentication Test")
print("-" * 80)
try:
    token = get_cached_or_new_token()
    print(f"✅ Token obtained: {token[:50]}...")
    print(f"   Token length: {len(token)} characters")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: LLM Chat Client Test
# ============================================================================
print("\n🤖 STEP 3: LLM Chat Client Initialization")
print("-" * 80)

if settings.llm_provider.lower() == "ollama":
    print("⚠️  Skipping enterprise LLM test - provider is set to 'ollama'")
    print("   Change LLM_PROVIDER to 'enterprise' in .env to test enterprise endpoints")
else:
    try:
        from llm.lm_interface import LLMInterface
        llm = LLMInterface()
        print(f"✅ LLM Client created: {llm.client_llm.__class__.__name__}")
        
        # ====================================================================
        # STEP 4: Test Simple Chat Completion
        # ====================================================================
        print("\n💬 STEP 4: Testing Chat Completion")
        print("-" * 80)
        print("Sending test message to LLM...")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello' if you can hear me."}
        ]
        
        response = llm.chat_completion(messages)
        print(f"✅ Response received: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ LLM Test Failed: {e}")
        print("\n📜 Full Error Details:")
        traceback.print_exc()
        
        # Additional debugging info
        print("\n🔍 Debugging Information:")
        print(f"   LLM_API_BASE: {settings.llm_api_base}")
        print(f"   LLM_DEPLOYMENT_NAME: {settings.llm_deployment_name}")
        
        # Try to extract more details from the error
        if "ConnectionError" in str(type(e).__name__):
            print("\n💡 This is a CONNECTION ERROR. Possible causes:")
            print("   1. Enterprise gateway is unreachable from this network")
            print("   2. Corporate proxy is blocking the connection")
            print("   3. SSL/TLS certificate issues")
            print("   4. VPN disconnected")
            
        elif "401" in str(e) or "403" in str(e):
            print("\n💡 This is an AUTHENTICATION ERROR. Possible causes:")
            print("   1. Token has expired")
            print("   2. Token format is incorrect")
            print("   3. Service account doesn't have access to LLM endpoint")
            
        elif "404" in str(e):
            print("\n💡 This is a NOT FOUND ERROR. Possible causes:")
            print("   1. LLM_API_BASE URL is incorrect")
            print("   2. LLM_DEPLOYMENT_NAME is incorrect")
            print("   3. Endpoint path format is wrong")
            
        elif "400" in str(e) or "Bad Request" in str(e):
            print("\n💡 This is a BAD REQUEST ERROR. Possible causes:")
            print("   1. Request format/parameters are incorrect")
            print("   2. API version mismatch")
            print("   3. Deployment name doesn't exist")

# ============================================================================
# STEP 5: Detailed Request Inspection
# ============================================================================
print("\n\n🔬 STEP 5: Manual Request Test (Low-level)")
print("-" * 80)

if settings.llm_provider.lower() != "ollama" and settings.llm_api_base:
    import requests
    import json
    
    # Construct the URL as the code does
    # For Azure OpenAI format
    url = f"{settings.llm_api_base.rstrip('/')}/chat/completions?api-version={settings.llm_api_version}"
    
    print(f"URL: {url}")
    print(f"Deployment: {settings.llm_deployment_name}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello."}
        ],
        "temperature": 0.2,
        "max_tokens": 100
    }
    
    print("\n📤 Sending request...")
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Response: {response.json()}")
        else:
            print(f"❌ FAILED!")
            print(f"Response Text: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        traceback.print_exc()

print("\n" + "=" * 80)
print("DEBUGGING COMPLETE")
print("=" * 80)
