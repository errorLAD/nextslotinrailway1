#!/usr/bin/env python
"""
Setup Cloudflare Custom Hostnames for all providers.

This script creates custom hostnames in Cloudflare for all service providers,
which automatically handles DNS routing without manual CNAME records.

No more Error 1014: CNAME Cross-User Banned!
"""

import os
import django
import requests
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.conf import settings
from providers.models import ServiceProvider
from providers.cloudflare_saas import create_custom_hostname

def get_cloudflare_credentials():
    """Get Cloudflare credentials from settings."""
    api_token = settings.CLOUDFLARE_API_TOKEN
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not api_token or not zone_id:
        print("❌ Error: Cloudflare credentials not configured!")
        print("\nSet these environment variables:")
        print("  - CLOUDFLARE_API_TOKEN")
        print("  - CLOUDFLARE_ZONE_ID")
        return None, None
    
    return api_token, zone_id

def verify_cloudflare_connection():
    """Verify connection to Cloudflare API."""
    api_token, zone_id = get_cloudflare_credentials()
    if not api_token or not zone_id:
        return False
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            f"https://api.cloudflare.com/client/v4/zones/{zone_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            zone_info = response.json()["result"]
            print(f"✅ Connected to Cloudflare zone: {zone_info['name']}")
            return True
        else:
            print(f"❌ Cloudflare error: {response.json()}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

def setup_custom_hostnames():
    """Setup Custom Hostnames for all providers."""
    
    print("\n" + "="*70)
    print("CLOUDFLARE CUSTOM HOSTNAMES SETUP")
    print("="*70)
    
    # Verify credentials
    print("\n1. Verifying Cloudflare credentials...")
    if not verify_cloudflare_connection():
        print("\n❌ Setup failed: Cannot connect to Cloudflare API")
        return False
    
    # Get all providers with custom domains
    print("\n2. Finding providers with custom domains...")
    providers = ServiceProvider.objects.filter(
        custom_domain__isnull=False
    ).exclude(custom_domain='')
    
    if not providers.exists():
        print("ℹ️  No providers with custom domains found")
        return True
    
    print(f"✅ Found {providers.count()} provider(s) with custom domain(s)")
    
    # Setup custom hostname for each provider
    print("\n3. Creating Custom Hostnames...")
    print("-" * 70)
    
    success_count = 0
    failed_count = 0
    
    for provider in providers:
        domain = provider.custom_domain
        print(f"\nSetting up: {domain} (Provider: {provider.business_name})")
        
        try:
            result = create_custom_hostname(domain, provider.pk)
            
            if result.get('success'):
                status = result.get('status', 'pending')
                hostname_id = result.get('id', 'N/A')
                
                print(f"  ✅ Success!")
                print(f"     - Hostname ID: {hostname_id}")
                print(f"     - Status: {status}")
                print(f"     - Next: Cloudflare will issue SSL cert (5-30 mins)")
                
                if status == 'pending':
                    print(f"     - Action: Domain is pending activation")
                    print(f"     - Check status at: https://dash.cloudflare.com/")
                
                success_count += 1
            else:
                error = result.get('error', 'Unknown error')
                print(f"  ❌ Failed: {error}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            failed_count += 1
    
    # Summary
    print("\n" + "-" * 70)
    print("SUMMARY")
    print("-" * 70)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Total: {providers.count()}")
    
    if failed_count == 0:
        print("\n🎉 All custom hostnames created successfully!")
        print("\nNext steps:")
        print("1. Wait 5-30 minutes for DNS propagation")
        print("2. Check Cloudflare dashboard for SSL certificate status")
        print("3. Test domains: https://yourprovider.com/")
        print("4. If domain doesn't work, check Cloudflare dashboard for errors")
        return True
    else:
        print("\n⚠️  Some providers failed. Check errors above.")
        print("\nCommon issues:")
        print("- Cloudflare API token invalid or missing permissions")
        print("- Zone ID is incorrect")
        print("- Domain already exists in Cloudflare")
        return False

def show_cloudflare_instructions():
    """Show instructions for enabling Custom Hostnames in Cloudflare."""
    print("\n" + "="*70)
    print("CLOUDFLARE CONFIGURATION CHECKLIST")
    print("="*70)
    
    print("""
✓ Have you enabled Custom Hostnames in Cloudflare?
  1. Go to: https://dash.cloudflare.com/
  2. Select your zone (nextslot.in)
  3. Navigate to: Settings → For SaaS
  4. Enable: "Custom Hostnames"
  5. Set fallback origin to: nextslot-app.ondigitalocean.app

✓ Have you created an API Token with correct permissions?
  1. Account → API Tokens
  2. Create Token with these permissions:
     - Zone.Custom Hostnames (Edit, Read)
     - Zone Resources: Include → Select nextslot.in
  3. Copy the token

✓ Have you set environment variables?
  1. Set CLOUDFLARE_API_TOKEN to your API token
  2. Set CLOUDFLARE_ZONE_ID to your zone ID
  3. (Optional) Set CLOUDFLARE_ACCOUNT_ID if needed

If you haven't done these, do them first, then run this script!
    """)

if __name__ == "__main__":
    # Show instructions
    show_cloudflare_instructions()
    
    # Ask for confirmation
    print("\nReady to setup Custom Hostnames? (yes/no): ", end="")
    response = input().strip().lower()
    
    if response != 'yes':
        print("❌ Setup cancelled")
        exit(1)
    
    # Run setup
    success = setup_custom_hostnames()
    
    if not success:
        exit(1)
