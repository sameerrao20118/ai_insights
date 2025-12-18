#!/usr/bin/env python3
"""
Test script for Gemini enterprise gateway.
This should work now that we're using CustomGeminiLangChainLLM.
"""
from llm.lm_interface import LLMInterface

print("=" * 80)
print("GEMINI ENTERPRISE GATEWAY TEST")
print("=" * 80)

print("\n🤖 Initializing LLM Interface...")
try:
    llm = LLMInterface()
    print(f"✅ LLM initialized successfully")
    print(f"   Client type: {type(llm.client_llm).__name__}")
    
    print("\n💬 Testing chat completion...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello! Gemini is working!' if you can hear me."}
    ]
    
    response = llm.chat_completion(messages)
    print(f"✅ Response received!")
    print(f"\n📝 Response: {response}")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
