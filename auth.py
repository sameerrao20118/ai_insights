from datetime import datetime, timezone
from typing import Optional

# Global cache for the token
# Format: {"token": str, "expiry": float}
_TOKEN_CACHE = {}

def get_cached_or_new_token() -> str:
    """
    Retrieves a valid JWT for Enterprise services.
    
    TODO: PASTE YOUR REAL AUTH LOGIC HERE FROM THE SCREENSHOTS.
    This module must implement the logic to:
    1. Check if a cached token exists and is valid (not expired).
    2. If not, request a new token using the Service Account credentials.
    3. Cache and return the token.
    """
    global _TOKEN_CACHE
    
    # Placeholder: return a dummy token if using "enterprise" mode without real logic
    # In a real scenario, this would fail against the corporate gateway.
    print("WARNING: Using placeholder auth token. Please implement auth.py!")
    return "DUMMY_ENTERPRISE_TOKEN"

def delete_token_cache() -> None:
    """Clears the cached token to force a refresh on the next call."""
    global _TOKEN_CACHE
    _TOKEN_CACHE.clear()
    print("Main token cache cleared.")
