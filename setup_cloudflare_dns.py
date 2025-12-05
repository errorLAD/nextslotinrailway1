#!/usr/bin/env python
"""
Setup Cloudflare DNS records for provider subdomains.

This script sets up CNAME records in Cloudflare for each provider's unique subdomain.

Each provider gets:
- A unique subdomain: {booking_url}.nextslot.in
- CNAME pointing to: nextslot-app.ondigitalocean.app

DNS Flow:
1. Provider custom domain: ramesh-salon.com
2. Provider CNAMEs: ramesh-salon.com → ramesh-salon.nextslot.in
3. Cloudflare has: ramesh-salon.nextslot.in → nextslot-app.ondigitalocean.app
4. User visits: ramesh-salon.com
5. Resolves to: nextslot-app.ondigitalocean.app (DigitalOcean app)
6. DigitalOcean routes based on Host header to correct provider
"""

import os
import sys
import django
import requests
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
sys.path.insert(0, str(BASE_DIR))
django.setup()

from django.conf import settings
from providers.models import ServiceProvider

# Cloudflare API
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"

def get_cloudflare_headers():
    """Get Cloudflare API headers."""
    return {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

def get_zone_id():
    """Get Cloudflare zone ID for nextslot.in"""
    return settings.CLOUDFLARE_ZONE_ID

def create_cname_record(name, target):
    """
    Create a CNAME record in Cloudflare.
    
    Args:
        name: Record name (e.g., 'ramesh-salon' for ramesh-salon.nextslot.in)
        target: Target domain (e.g., nextslot-app.ondigitalocean.app)
    
    Returns:
        dict: API response
    """
    url = f"{CLOUDFLARE_API_BASE}/zones/{get_zone_id()}/dns_records"
    
    data = {
        "type": "CNAME",
        "name": f"{name}.nextslot.in",  # Full domain name
        "content": target,
        "ttl": 3600,
        "proxied": False  # Set to True if you want Cloudflare proxy (orange cloud)
    }
    
    headers = get_cloudflare_headers()
    
    print(f"Creating CNAME: {name}.nextslot.in → {target}")
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    
    if result.get('success'):
        print(f"  ✓ Created successfully (ID: {result['result']['id']})")
        return result
    else:
        print(f"  ✗ Failed: {result.get('errors', [{}])[0].get('message', 'Unknown error')}")
        return result

def get_existing_records():
    """Get all existing CNAME records from Cloudflare."""
    url = f"{CLOUDFLARE_API_BASE}/zones/{get_zone_id()}/dns_records?type=CNAME"
    headers = get_cloudflare_headers()
    
    response = requests.get(url, headers=headers)
    result = response.json()
    
    if result.get('success'):
        return {record['name']: record for record in result['result']}
    else:
        print(f"Failed to fetch records: {result}")
        return {}

def delete_cname_record(record_id):
    """Delete a CNAME record from Cloudflare."""
    url = f"{CLOUDFLARE_API_BASE}/zones/{get_zone_id()}/dns_records/{record_id}"
    headers = get_cloudflare_headers()
    
    response = requests.delete(url, headers=headers)
    result = response.json()
    
    return result.get('success', False)

def main():
    """Main function to setup provider subdomains in Cloudflare."""
    
    print("\n" + "="*80)
    print("SETUP CLOUDFLARE DNS RECORDS FOR PROVIDER SUBDOMAINS")
    print("="*80 + "\n")
    
    # Check Cloudflare configuration
    if not settings.CLOUDFLARE_API_TOKEN:
        print("✗ CLOUDFLARE_API_TOKEN not configured")
        return
    
    if not settings.CLOUDFLARE_ZONE_ID:
        print("✗ CLOUDFLARE_ZONE_ID not configured")
        return
    
    # Get DigitalOcean app domain
    do_domain = getattr(settings, 'DIGITALOCEAN_APP_DOMAIN', 'nextslot-app.ondigitalocean.app')
    base_domain = getattr(settings, 'PROVIDER_SUBDOMAIN_BASE', 'nextslot.in')
    
    print(f"Base Domain: {base_domain}")
    print(f"DigitalOcean App: {do_domain}\n")
    
    # Get all service providers
    providers = ServiceProvider.objects.filter(
        custom_domain__isnull=False
    ).exclude(custom_domain='')
    
    if not providers.exists():
        print("No service providers with custom domains found.")
        return
    
    print(f"Found {providers.count()} provider(s) with custom domains\n")
    
    # Get existing records
    existing_records = get_existing_records()
    print(f"Existing CNAME records in Cloudflare: {len(existing_records)}\n")
    
    # Setup each provider
    for provider in providers:
        booking_url = provider.unique_booking_url
        subdomain_name = f"{booking_url}.{base_domain}"
        
        print(f"\n{'─'*80}")
        print(f"Provider: {provider.business_name}")
        print(f"Booking URL: {booking_url}")
        print(f"Custom Domain: {provider.custom_domain}")
        print(f"Subdomain: {subdomain_name}")
        print(f"{'─'*80}")
        
        # Check if record already exists
        if subdomain_name in existing_records:
            existing = existing_records[subdomain_name]
            print(f"  ℹ Record already exists")
            print(f"    Current target: {existing.get('content')}")
            
            if existing.get('content') != do_domain:
                print(f"    Expected target: {do_domain}")
                print(f"    WARNING: Target mismatch! Consider updating.")
        else:
            # Create new record
            result = create_cname_record(booking_url, do_domain)
            if result.get('success'):
                print(f"  DNS Configuration:")
                print(f"    Name: {subdomain_name}")
                print(f"    Type: CNAME")
                print(f"    Content: {do_domain}")
                print(f"    Provider should CNAME their domain to: {subdomain_name}")
                print(f"    Example: {provider.custom_domain} → {subdomain_name}")
    
    print(f"\n{'='*80}")
    print("SETUP COMPLETE")
    print("="*80 + "\n")
    
    print("Next Steps for Each Provider:")
    print("1. Each provider gets a unique subdomain on nextslot.in")
    print("2. Provider should CNAME their custom domain to their unique subdomain")
    print("   Example: ramesh-salon.com CNAME → ramesh-salon.nextslot.in")
    print("3. Verify with: nslookup {custom_domain}")
    print("4. Once DNS propagates, domain will be live!\n")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
