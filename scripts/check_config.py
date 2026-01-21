#!/usr/bin/env python3
"""
Quick check script to verify if LLM_PROVIDER is correctly set.
"""
import sys
from pathlib import Path

# Add parent directory to path so imports work from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

print("=" * 60)
print("QUICK CONFIGURATION CHECK")
print("=" * 60)

print(f"\n🔧 Current Configuration:")
print(f"   LLM_PROVIDER: '{settings.llm_provider}'")
print(f"   LLM_API_BASE: '{settings.llm_api_base}'")

if settings.llm_provider.lower() == "ollama":
    print(f"\n⚠️  WARNING!")
    print(f"   Your LLM_PROVIDER is set to 'ollama'")
    print(f"   This means the app will try to connect to:")
    print(f"   → {settings.ollama_api_base}")
    print(f"\n   For enterprise mode, update your .env:")
    print(f"   LLM_PROVIDER=enterprise")
else:
    print(f"\n✅ LLM_PROVIDER is set to '{settings.llm_provider}'")
    print(f"   The app will use enterprise endpoints")
    
print("\n" + "=" * 60)
