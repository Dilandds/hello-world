#!/usr/bin/env python3
"""
License Key Generation Script

Generates cryptographically secure license keys for the STL 3D Viewer application.
"""

import uuid
import sys
import argparse
from datetime import datetime


def generate_license_key(prefix: str = "STL") -> str:
    """
    Generate a license key in the format: PREFIX-XXXX-XXXX-XXXX-XXXX
    
    Args:
        prefix: Prefix for the license key (default: "STL")
    
    Returns:
        Formatted license key string
    """
    # Generate UUID4 (random UUID)
    uuid_str = str(uuid.uuid4()).replace('-', '').upper()
    
    # Format as: PREFIX-XXXX-XXXX-XXXX-XXXX
    formatted = f"{prefix}-{uuid_str[0:4]}-{uuid_str[4:8]}-{uuid_str[8:12]}-{uuid_str[12:16]}"
    
    return formatted


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate license keys for STL 3D Viewer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_license_key.py
  python generate_license_key.py --prefix STL
  python generate_license_key.py --count 5
  python generate_license_key.py --prefix STL --count 10
        """
    )
    
    parser.add_argument(
        '--prefix',
        type=str,
        default='STL',
        help='Prefix for license keys (default: STL)'
    )
    
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of license keys to generate (default: 1)'
    )
    
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format (for copying to Gist)'
    )
    
    args = parser.parse_args()
    
    # Generate keys
    keys = []
    for _ in range(args.count):
        key = generate_license_key(prefix=args.prefix)
        keys.append(key)
    
    # Output
    if args.json:
        # JSON format for Gist
        import json
        output = {
            "valid_keys": keys,
            "updated": datetime.now().isoformat() + "Z"
        }
        print(json.dumps(output, indent=2))
    else:
        # Plain text format
        print("Generated License Keys:")
        print("=" * 50)
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key}")
        print("=" * 50)
        print(f"\nTotal: {len(keys)} key(s)")
        print("\nTo add these to your GitHub Gist:")
        print("1. Go to your Gist: https://gist.github.com/USERNAME/GIST_ID")
        print("2. Click 'Edit'")
        print("3. Add the keys to the 'valid_keys' array")
        print("4. Update the 'updated' timestamp")
        print("5. Click 'Update public gist'")


if __name__ == "__main__":
    main()
