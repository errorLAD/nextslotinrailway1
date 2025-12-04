"""Test Cloudflare API configuration"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

import requests
from django.conf import settings
from providers.models import ServiceProvider

def test_cloudflare_api():
    print('=== Cloudflare Configuration Check ===')
    print(f'API Token: {settings.CLOUDFLARE_API_TOKEN[:20]}...' if settings.CLOUDFLARE_API_TOKEN else 'NOT SET')
    print(f'Zone ID: {settings.CLOUDFLARE_ZONE_ID}')
    print(f'CNAME Target: {settings.CLOUDFLARE_CNAME_TARGET}')
    print()
    
    zone_id = settings.CLOUDFLARE_ZONE_ID
    headers = {
        'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Test 1: Get zone details
    print('=== Test 1: Zone Details ===')
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}'
    response = requests.get(url, headers=headers, timeout=30)
    data = response.json()
    
    if data.get('success'):
        zone = data.get('result', {})
        print(f'Zone Name: {zone.get("name")}')
        print(f'Zone Status: {zone.get("status")}')
        print('API Connection: SUCCESS ✓')
    else:
        print(f'API Error: {data.get("errors")}')
        return
    
    print()
    
    # Test 2: List existing custom hostnames
    print('=== Test 2: Existing Custom Hostnames ===')
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames'
    response = requests.get(url, headers=headers, timeout=30)
    data = response.json()
    
    if data.get('success'):
        hostnames = data.get('result', [])
        if hostnames:
            for h in hostnames:
                print(f"  - {h.get('hostname')} | Status: {h.get('status')} | SSL: {h.get('ssl', {}).get('status')}")
        else:
            print('  No custom hostnames configured yet')
    else:
        print(f'  Error: {data.get("errors")}')
    
    print()
    
    # Test 3: Check providers with custom domains
    print('=== Test 3: Providers with Custom Domains ===')
    providers = ServiceProvider.objects.exclude(custom_domain__isnull=True).exclude(custom_domain='')
    if providers.exists():
        for p in providers:
            print(f"  - {p.business_name}: {p.custom_domain} | Verified: {p.domain_verified}")
    else:
        print('  No providers have custom domains configured')

if __name__ == '__main__':
    test_cloudflare_api()
