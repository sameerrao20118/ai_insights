from datetime import datetime, timezone
from typing import Optional
import base64
import json
import os
import time
import requests

# Global cache for the token
# Format: {"token": str, "expiry": float}
_TOKEN_CACHE = {}

TOKEN_FILE = "token.json"
DEFAULT_TTL = 3600  # 1 hour, a safer default for enterprise tokens


def save_token(token: str, ttl: int) -> None:
    """Saves the token + timestamp + TTL to a cache file."""
    with open(TOKEN_FILE, "w") as file:
        json.dump({"access_token": token, "timestamp": time.time(), "ttl": ttl}, file)


def load_token():
    """Loads token data from the cache file if it exists."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as file:
                data = json.load(file)
                return data.get("access_token"), data.get("timestamp"), data.get("ttl", DEFAULT_TTL)
        except (json.JSONDecodeError, KeyError):
            # If the file is corrupted or has an unexpected format, treat it as non-existent
            return None, None, None
    return None, None, None


def is_token_valid(timestamp: float, ttl: int) -> bool:
    """Checks if the cached token is still within its time-to-live."""
    if not timestamp:
        return False
    return (time.time() - timestamp) < ttl


def b64e(s: str) -> str:
    """Encodes a string to base64."""
    return base64.b64encode(s.encode()).decode()


def get_jwt(url: str, encoded_pass: str) -> str:
    """
    API call to the auth service to get a new JWT.
    
    Handles non-2xx status codes (404/403) separately. 
    A more robust way to handle JSON vs. non-JSON errors gracefully.
    """
    headers = {"authorization": "Basic " + encoded_pass}
    
    try:
        response = requests.post(url, headers=headers, data={}, verify=False)
        
        print(f"DEBUG: Auth server response status code: {response.status_code}")
        
        # Check for non-2xx status codes first. This handles server errors gracefully.
        if response.status_code != 200:
            response.raise_for_status()
        
        # If it's a non-2xx, check if the response even has content:
        if not response.text.strip():
            print("ERROR: Auth server returned an empty response body.")
            return ""  # Return empty string to be handled by the caller
        
        # Now, attempt to parse JSON
        try:
            return response.json().get("access_token", "")
        except requests.exceptions.JSONDecodeError:
            # If it fails, it's not JSON. Return the raw text.
            # This is useful for the server returns the token as plain text
            print("ERROR: Auth server returned an empty response body.")
            return response.text.strip()
            
    except requests.exceptions.RequestException as e:
        # This will catch connection errors, timeouts, etc.
        print(f"FATAL: Could not get JWT from auth service: {e}")
        raise


def delete_token_cache():
    """
    Deletes the token cache file if it exists.
    This is called by other modules when they receive a 401/403 error,
    forcing a fresh token fetch on the next attempt.
    """
    if os.path.exists(TOKEN_FILE):
        try:
            os.remove(TOKEN_FILE)
            print("✓ Stale authentication token cache has been deleted.")
        except OSError as e:
            print(f"⚠ Error deleting token cache file: {e}")


def get_cached_or_new_token() -> str:
    """The main function: returns a valid token from cache or fetches a new one."""
    from config.settings import settings
    
    token, timestamp, cached_ttl = load_token()
    
    if token and timestamp and is_token_valid(timestamp, cached_ttl):
        print("✓ Using cached authentication token.")
        return token
    
    print("⚠ No valid cached token found. Fetching a new one...")
    
    service_account = os.environ.get("SERVICE_ACCOUNT", settings.service_account)
    service_account_pass = os.environ.get("SERVICE_ACCOUNT_PASS", settings.service_account_pass)
    auth_url = os.environ.get("AUTH_URL", settings.auth_url)
    
    if not all([service_account, service_account_pass, auth_url]):
        raise ValueError("SERVICE_ACCOUNT, SERVICE_ACCOUNT_PASS, and AUTH_URL must be set in your .env file")
    
    encoded_pass = b64e(f"{service_account}:{service_account_pass}")
    new_token = get_jwt(auth_url, encoded_pass)
    
    if not new_token:
        raise ValueError("Authentication failed: Received an empty token.")
    
    save_token(new_token, DEFAULT_TTL)
    print("✓ New authentication token fetched and cached.")
    return new_token

