import sys
import os
from pathlib import Path

# Add parent directory to path so imports work from scripts/
sys.path.insert(0, str(Path(__file__).parent.parent))

print("--- 1. Testing Dependencies ---")
try:
    import langchain_core
    print("✅ langchain_core imported")
    import langchain_openai
    print("✅ langchain_openai imported")
    import pydantic_settings
    print("✅ pydantic_settings imported")
except ImportError as e:
    print(f"❌ Dependency missing: {e}")
    sys.exit(1)

print("\n--- 2. Testing Configuration ---")
try:
    from config.settings import settings
    print(f"✅ Settings loaded. Provider: {settings.llm_provider}")
except Exception as e:
    print(f"❌ Configuration load failed: {e}")
    sys.exit(1)

print("\n--- 3. Testing LLM Interface (Initialization) ---")
try:
    from llm.lm_interface import LLMInterface
    llm = LLMInterface()
    print("✅ LLMInterface initialized successfully")
except Exception as e:
    print(f"❌ LLMInterface init failed: {e}")
    sys.exit(1)

print("\n--- 4. Testing Service Integration (Mock) ---")
try:
    # We can't easily query the real DB without data, but we can check if functions import and run
    import services
    print("✅ services module imported")
    
    # Mock payload for structure check
    from llm.lm_interface import CatalogueChatAnswer
    print("✅ Pydantic models importable")
    
except Exception as e:
    print(f"❌ Service integration check failed: {e}")
    sys.exit(1)

print("\n--- 5. Testing API Import ---")
try:
    from api import app
    print("✅ FastAPI app object imported successfully")
except Exception as e:
    print(f"❌ API import failed: {e}")
    sys.exit(1)

print("\n🎉 ALL CHECKS PASSED")
