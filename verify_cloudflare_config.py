#!/usr/bin/env python
"""
Verify Cloudflare for SaaS Configuration

This script checks if all Cloudflare settings are properly configured.
Run this BEFORE running setup_cloudflare_custom_hostnames.py
"""

import os
import sys
import requests
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.conf import settings

def check_settings():
    """Check if Cloudflare settings are configured."""
    print("\n" + "="*70)
    print("CHECKING CLOUDFLARE SETTINGS")
    print("="*70)
    
    issues = []
    
    # Check API Token
    api_token = settings.CLOUDFLARE_API_TOKEN
    print("\n1. CLOUDFLARE_API_TOKEN:")
    if not api_token:
        print("   ❌ NOT SET")
        issues.append("CLOUDFLARE_API_TOKEN is not configured")
    elif len(api_token) < 20:
        print("   ❌ TOO SHORT (looks invalid)")
        issues.append("CLOUDFLARE_API_TOKEN looks invalid (too short)")
    else:
        # Show partial token (for security)
        masked = api_token[:10] + "*" * 20
        print(f"   ✅ SET ({masked})")
    
    # Check Zone ID
    zone_id = settings.CLOUDFLARE_ZONE_ID
    print("\n2. CLOUDFLARE_ZONE_ID:")
    if not zone_id:
        print("   ❌ NOT SET")
        issues.append("CLOUDFLARE_ZONE_ID is not configured")
    elif len(zone_id) != 32:
        print(f"   ⚠️  UNEXPECTED LENGTH ({len(zone_id)} chars, expected 32)")
        print(f"   Zone ID: {zone_id}")
    else:
        print(f"   ✅ SET ({zone_id})")
    
    # Check Account ID
    account_id = settings.CLOUDFLARE_ACCOUNT_ID
    print("\n3. CLOUDFLARE_ACCOUNT_ID:")
    if not account_id:
        print("   ⚠️  NOT SET (optional)")
    elif len(account_id) != 32:
        print(f"   ⚠️  UNEXPECTED LENGTH ({len(account_id)} chars, expected 32)")
    else:
        print(f"   ✅ SET ({account_id})")
    
    # Check default domain
    default_domain = settings.DEFAULT_DOMAIN
    print(f"\n4. DEFAULT_DOMAIN:")
    print(f"   ✅ SET ({default_domain})")
    
    # Check DigitalOcean domain
    do_domain = settings.DIGITALOCEAN_APP_DOMAIN
    print(f"\n5. DIGITALOCEAN_APP_DOMAIN:")
    if do_domain:
        print(f"   ✅ SET ({do_domain})")
    else:
        print(f"   ❌ NOT SET")
        issues.append("DIGITALOCEAN_APP_DOMAIN is not configured")
    
    return issues


def test_cloudflare_api():
    """Test connection to Cloudflare API."""
    print("\n" + "="*70)
    print("TESTING CLOUDFLARE API CONNECTION")
    print("="*70)
    
    api_token = settings.CLOUDFLARE_API_TOKEN
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not api_token or not zone_id:
        print("\n❌ Cannot test: Settings not configured")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    print("\n1. Testing zone access...")
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            zone_info = response.json()
            if zone_info.get("success"):
                zone_name = zone_info["result"]["name"]
                print(f"   ✅ Connected to zone: {zone_name}")
                
                # Check if Custom Hostnames is available
                plan = zone_info["result"].get("plan", {})
                plan_name = plan.get("name", "Unknown")
                print(f"   Zone Plan: {plan_name}")
                
                return True
            else:
                errors = zone_info.get("errors", [])
                print(f"   ❌ API error: {errors[0].get('message')}")
                return False
        elif response.status_code == 401:
            print("   ❌ Invalid API token (401 Unauthorized)")
            print("   Check your CLOUDFLARE_API_TOKEN setting")
            return False
        elif response.status_code == 404:
            print("   ❌ Zone not found (404)")
            print("   Check your CLOUDFLARE_ZONE_ID setting")
            return False
        else:
            print(f"   ❌ HTTP {response.status_code}: {response.text}")
            return False
            
    except requests.Timeout:
        print("   ❌ Connection timeout - check internet connection")
        return False
    except requests.ConnectionError as e:
        print(f"   ❌ Connection error: {e}")
        return False


def check_custom_hostnames_feature():
    """Check if Custom Hostnames feature is available."""
    print("\n" + "="*70)
    print("CHECKING CUSTOM HOSTNAMES FEATURE")
    print("="*70)
    
    api_token = settings.CLOUDFLARE_API_TOKEN
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not api_token or not zone_id:
        print("\n❌ Cannot check: Settings not configured")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    print("\n1. Checking for existing custom hostnames...")
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                hostnames = data.get("result", [])
                count = len(hostnames)
                print(f"   ✅ Custom Hostnames available!")
                print(f"   Current hostnames: {count}")
                
                if hostnames:
                    print("\n   Existing custom hostnames:")
                    for h in hostnames[:5]:  # Show first 5
                        hostname = h.get("hostname", "Unknown")
                        status = h.get("status", "Unknown")
                        print(f"     - {hostname} (Status: {status})")
                
                return True
            else:
                errors = data.get("errors", [])
                print(f"   ❌ API error: {errors[0].get('message')}")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def check_api_token_permissions():
    """Check API token permissions."""
    print("\n" + "="*70)
    print("CHECKING API TOKEN PERMISSIONS")
    print("="*70)
    
    api_token = settings.CLOUDFLARE_API_TOKEN
    
    if not api_token:
        print("\n❌ API token not configured")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    print("\n1. Checking token status...")
    try:
        response = requests.get(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                token_info = data.get("result", {})
                status = token_info.get("status", "Unknown")
                print(f"   ✅ Token is valid (Status: {status})")
                
                print("\n2. Token permissions:")
                permissions = token_info.get("permissions", [])
                if permissions:
                    for perm in permissions:
                        print(f"     - {perm}")
                    
                    # Check for required permissions
                    required = "Zone.Custom Hostnames"
                    found = any(required in p for p in permissions)
                    if found:
                        print(f"\n   ✅ Has '{required}' permission")
                        return True
                    else:
                        print(f"\n   ⚠️  Missing '{required}' permission")
                        print("   Consider adding this permission to your API token")
                        return False
                else:
                    print("   ⚠️  No permissions found")
                    return False
            else:
                print("   ❌ Invalid token")
                return False
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def show_recommendations(issues):
    """Show recommendations based on findings."""
    if not issues:
        print("\n" + "="*70)
        print("✅ ALL CHECKS PASSED!")
        print("="*70)
        print("\nYou're ready to run: python setup_cloudflare_custom_hostnames.py")
        return
    
    print("\n" + "="*70)
    print("⚠️  ISSUES FOUND")
    print("="*70)
    
    for issue in issues:
        print(f"\n❌ {issue}")
    
    print("\n" + "-"*70)
    print("RECOMMENDATIONS:")
    print("-"*70)
    
    if "CLOUDFLARE_API_TOKEN" in str(issues):
        print("""
1. Create API Token:
   - Go to: https://dash.cloudflare.com/
   - Account → API Tokens → Create Token
   - Permissions: Zone.Custom Hostnames (Edit, Read)
   - Zone: Select nextslot.in
   - Copy the token
   
2. Set environment variable:
   - CLOUDFLARE_API_TOKEN=<your_token>
""")
    
    if "CLOUDFLARE_ZONE_ID" in str(issues):
        print("""
1. Get Zone ID:
   - Go to: https://dash.cloudflare.com/
   - Select nextslot.in zone
   - Right sidebar shows: Zone ID
   - Copy it
   
2. Set environment variable:
   - CLOUDFLARE_ZONE_ID=<your_zone_id>
""")
    
    if "DIGITALOCEAN_APP_DOMAIN" in str(issues):
        print("""
1. Get DigitalOcean app domain:
   - Go to: https://cloud.digitalocean.com/
   - App Platform → Your app
   - Copy the app domain
   
2. Set environment variable:
   - DIGITALOCEAN_APP_DOMAIN=<your_app_domain>
""")


def main():
    """Run all checks."""
    print("\n🔍 CLOUDFLARE FOR SAAS VERIFICATION")
    
    # Check settings
    issues = check_settings()
    
    # Test API if configured
    if not any("not configured" in str(i).lower() for i in issues[:2]):
        if not test_cloudflare_api():
            issues.append("Cannot connect to Cloudflare API")
        else:
            # Test additional features
            check_custom_hostnames_feature()
            check_api_token_permissions()
    
    # Show recommendations
    show_recommendations(issues)
    
    # Exit code
    if issues:
        print("\n" + "="*70)
        print("❌ Fix the issues above, then run this script again")
        print("="*70)
        sys.exit(1)
    else:
        print("\n" + "="*70)
        print("Ready to setup custom hostnames!")
        print("Run: python setup_cloudflare_custom_hostnames.py")
        print("="*70)


if __name__ == "__main__":
    main()
