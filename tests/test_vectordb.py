#!/usr/bin/env python3
"""
Test script to verify Vector DB Manager initialization.
Run this on your enterprise machine as the final integration test.
"""
from storage.vector_db_manager import VectorDBManager

print("=" * 60)
print("VECTOR DB MANAGER TEST")
print("=" * 60)

print(f"\n💾 Initializing Vector DB Manager...")
try:
    vdb = VectorDBManager()
    print(f"   ✅ VectorDBManager initialized successfully!")
    print(f"   Collection: {vdb.collection.name}")
    print(f"   Count: {vdb.collection.count()} documents")
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    print("\n📜 Full traceback:")
    import traceback
    traceback.print_exc()
    
    print("\n💡 Common Causes:")
    print("   1. Authentication failure (run test_auth.py first)")
    print("   2. LLM initialization failure (run test_llm.py second)")
    print("   3. ChromaDB path issues")
    print("   4. Proxy/SSL certificate issues")
    
print("\n" + "=" * 60)
