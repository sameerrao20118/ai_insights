#!/usr/bin/env python3
"""
Test script to verify LLM interface initialization.
Run this on your enterprise machine after auth test passes.
"""
from llm.lm_interface import LLMInterface

print("=" * 60)
print("LLM INTERFACE TEST")
print("=" * 60)

print(f"\n🤖 Initializing LLM Interface...")
try:
    llm = LLMInterface()
    print(f"   ✅ LLM initialized successfully")
    print(f"   Provider: {llm.client_llm.__class__.__name__}")
    
    print(f"\n🔢 Testing embeddings...")
    result = llm.embed_texts(["test"])
    print(f"   ✅ Embeddings work!")
    print(f"   Generated {len(result)} embeddings")
    print(f"   Embedding dimension: {len(result[0]) if result else 0}")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print("\n📜 Full traceback:")
    import traceback
    traceback.print_exc()
    
print("\n" + "=" * 60)
