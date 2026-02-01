"""
License Key Validator Module

Validates license keys against a GitHub Gist containing valid keys.
Supports online validation with offline caching.
"""

import json
import sys
import requests
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple

# Configuration: GitHub Gist URL for valid license keys
# TODO: Replace with your actual GitHub Gist raw URL
# Format: https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/FILENAME/valid_licenses.json
# Example: https://gist.githubusercontent.com/Dilandds/bd5c8db0157c16dc2473a8d1fe368b44/raw/valid_licenses.json
GIST_URL = "https://gist.githubusercontent.com/Dilandds/bd5c8db0157c16dc2473a8d1fe368b44/raw/valid_licenses.json"

# Timeout for HTTP requests (seconds)
REQUEST_TIMEOUT = 10

# Cache expiration time (days) - use cached keys if fetched within this time
CACHE_EXPIRY_DAYS = 7


def get_config_directory() -> Path:
    """Get the configuration directory for storing license data."""
    if sys.platform == "darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / "ECTOFORM"
    elif sys.platform == "win32":  # Windows
        config_dir = Path.home() / "AppData" / "Local" / "ECTOFORM"
    else:  # Linux
        config_dir = Path.home() / ".config" / "ectoform"
    
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_license_storage_path() -> Path:
    """Get the path to the license storage file."""
    return get_config_directory() / "license.json"


def get_stored_license_key() -> Optional[str]:
    """Get the stored license key from local storage."""
    storage_path = get_license_storage_path()
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("license_key")
    except (json.JSONDecodeError, IOError, KeyError):
        return None


def store_license_key(license_key: str, valid_keys: Optional[List[str]] = None) -> None:
    """Store the license key and optionally cache valid keys."""
    storage_path = get_license_storage_path()
    config_dir = get_config_directory()
    config_dir.mkdir(parents=True, exist_ok=True)
    
    data = {
        "license_key": license_key,
        "validated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    if valid_keys:
        data["cached_valid_keys"] = valid_keys
        data["cached_at"] = datetime.now(timezone.utc).isoformat()
    
    try:
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except IOError:
        # If we can't write, that's okay - validation will still work
        pass


def get_cached_valid_keys() -> Optional[List[str]]:
    """Get cached valid keys from local storage."""
    storage_path = get_license_storage_path()
    if not storage_path.exists():
        return None
    
    try:
        with open(storage_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Check if cache is still valid
            cached_at_str = data.get("cached_at")
            if cached_at_str:
                cached_at = datetime.fromisoformat(cached_at_str.replace('Z', '+00:00'))
                age = (datetime.now(timezone.utc) - cached_at).days
                if age > CACHE_EXPIRY_DAYS:
                    return None  # Cache expired
            
            return data.get("cached_valid_keys")
    except (json.JSONDecodeError, IOError, KeyError, ValueError):
        return None


def fetch_valid_keys_from_gist(gist_url: str = GIST_URL) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Fetch valid license keys from GitHub Gist.
    
    Returns:
        Tuple of (list of valid keys, error message)
        If successful: (keys_list, None)
        If error: (None, error_message)
    """
    try:
        response = requests.get(gist_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        valid_keys = data.get("valid_keys", [])
        
        if not isinstance(valid_keys, list):
            return None, "Invalid Gist format: 'valid_keys' must be a list"
        
        return valid_keys, None
        
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please check your internet connection."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check your internet connection."
    except requests.exceptions.HTTPError as e:
        return None, f"HTTP error: {e.response.status_code}"
    except json.JSONDecodeError:
        return None, "Invalid JSON response from Gist"
    except KeyError:
        return None, "Invalid Gist format: 'valid_keys' key not found"
    except Exception as e:
        return None, f"Error fetching keys: {str(e)}"


def validate_license_key(license_key: str, valid_keys: List[str]) -> bool:
    """
    Validate a license key against a list of valid keys.
    
    Args:
        license_key: The license key to validate
        valid_keys: List of valid license keys
    
    Returns:
        True if key is valid, False otherwise
    """
    if not license_key or not valid_keys:
        return False
    
    # Strip whitespace and normalize
    license_key = license_key.strip().upper()
    
    # Check if key exists in valid keys list
    normalized_valid_keys = [key.strip().upper() for key in valid_keys]
    return license_key in normalized_valid_keys


def check_license_validity(license_key: str, use_cache: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if a license key is valid.
    
    Tries online validation first, falls back to cached keys if offline.
    
    Args:
        license_key: The license key to validate
        use_cache: If True, use cached keys if online validation fails
    
    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, None)
        If invalid: (False, error_message)
    """
    if not license_key:
        return False, "License key is empty"
    
    # Try online validation first
    valid_keys, error = fetch_valid_keys_from_gist()
    
    if valid_keys is not None:
        # Online validation successful
        is_valid = validate_license_key(license_key, valid_keys)
        
        # Update cache
        store_license_key(license_key, valid_keys)
        
        if is_valid:
            return True, None
        else:
            return False, "Invalid license key"
    
    # Online validation failed, try cache
    if use_cache:
        cached_keys = get_cached_valid_keys()
        if cached_keys:
            is_valid = validate_license_key(license_key, cached_keys)
            if is_valid:
                return True, None
            else:
                return False, f"Invalid license key (offline mode: {error})"
    
    # Both online and cache failed
    return False, error or "Unable to validate license key"


def is_license_valid_stored() -> bool:
    """
    Check if the stored license key is valid.
    
    Returns:
        True if stored key exists and is valid, False otherwise
    """
    stored_key = get_stored_license_key()
    if not stored_key:
        return False
    
    is_valid, _ = check_license_validity(stored_key, use_cache=True)
    return is_valid


# For testing/development
if __name__ == "__main__":
    print("License Validator Module")
    print(f"Config directory: {get_config_directory()}")
    print(f"Storage path: {get_license_storage_path()}")
    
    stored_key = get_stored_license_key()
    print(f"Stored key: {stored_key}")
    
    if stored_key:
        is_valid, error = check_license_validity(stored_key)
        print(f"Valid: {is_valid}, Error: {error}")
