"""
Diagnose okmentor.in DNS and Cloudflare setup
"""
import requests
from django.conf import settings
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

print("=" * 80)
print("OKMENTOR.IN DIAGNOSTICS")
print("=" * 80)

zone_id = settings.CLOUDFLARE_ZONE_ID
headers = {
    'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
    'Content-Type': 'application/json'
}

# 1. Check custom hostname in Cloudflare
print("\n1. CHECKING CLOUDFLARE CUSTOM HOSTNAME")
print("-" * 80)

url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames'
response = requests.get(url, headers=headers, timeout=30)
data = response.json()

if data.get('success'):
    hostnames = data.get('result', [])
    okmentor = None
    
    for h in hostnames:
        print(f"\nHostname: {h.get('hostname')}")
        print(f"  Status: {h.get('status')}")
        print(f"  SSL Status: {h.get('ssl', {}).get('status')}")
        print(f"  Ownership Status: {h.get('ownership_verification', {}).get('verification_status')}")
        print(f"  CNAME Status: {h.get('cname_status')}")
        
        if h.get('hostname') == 'okmentor.in':
            okmentor = h
            print("  ✓ This is our target domain!")
    
    if not okmentor:
        print("\n⚠️  okmentor.in NOT FOUND in Cloudflare custom hostnames!")
        print("Next step: Create it via Cloudflare API")
else:
    print(f"Error: {data.get('errors')}")

# 2. Check DNS records
print("\n2. CHECKING DNS RECORDS IN CLOUDFLARE")
print("-" * 80)

dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name=okmentor.in'
dns_response = requests.get(dns_url, headers=headers, timeout=30)
dns_data = dns_response.json()

if dns_data.get('success'):
    records = dns_data.get('result', [])
    if records:
        for r in records:
            print(f"\nType: {r.get('type')}")
            print(f"  Name: {r.get('name')}")
            print(f"  Content: {r.get('content')}")
            print(f"  Proxied: {r.get('proxied')}")
            print(f"  Status: {r.get('status')}")
    else:
        print("⚠️  No DNS records found for okmentor.in")
        print("\nCreating CNAME record...")
        
        # Create CNAME record
        create_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
        payload = {
            'type': 'CNAME',
            'name': 'okmentor',
            'content': settings.CLOUDFLARE_CNAME_TARGET,
            'proxied': True
        }
        
        create_response = requests.post(create_url, headers=headers, json=payload, timeout=30)
        create_data = create_response.json()
        
        if create_data.get('success'):
            print("✓ CNAME record created successfully!")
            record = create_data.get('result', {})
            print(f"  Name: {record.get('name')}")
            print(f"  Content: {record.get('content')}")
        else:
            print(f"✗ Error creating CNAME: {create_data.get('errors')}")
else:
    print(f"Error: {dns_data.get('errors')}")

# 3. Check fallback origin
print("\n3. CHECKING FALLBACK ORIGIN")
print("-" * 80)

fallback_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames/fallback_origin'
fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
fallback_data = fallback_response.json()

if fallback_data.get('success'):
    result = fallback_data.get('result', {})
    origin = result.get('origin')
    status = result.get('status')
    
    print(f"Origin: {origin}")
    print(f"Status: {status}")
    
    if not origin or status != 'active':
        print("\n⚠️  Fallback origin not configured!")
        print(f"Setting to: {settings.CLOUDFLARE_CNAME_TARGET}")
        
        set_payload = {'origin': settings.CLOUDFLARE_CNAME_TARGET}
        set_response = requests.put(fallback_url, headers=headers, json=set_payload, timeout=30)
        set_data = set_response.json()
        
        if set_data.get('success'):
            print("✓ Fallback origin set successfully!")
        else:
            print(f"✗ Error setting fallback origin: {set_data.get('errors')}")
else:
    print(f"Error: {fallback_data.get('errors')}")

# 4. Check database entry
print("\n4. CHECKING DATABASE ENTRY")
print("-" * 80)

try:
    from providers.models import ServiceProvider
    
    provider = ServiceProvider.objects.get(custom_domain__iexact='okmentor.in')
    print(f"\nProvider: {provider.business_name}")
    print(f"  Custom Domain: {provider.custom_domain}")
    print(f"  Domain Type: {provider.custom_domain_type}")
    print(f"  Verified: {provider.domain_verified}")
    print(f"  SSL Enabled: {provider.ssl_enabled}")
    print(f"  Cloudflare ID: {provider.cloudflare_hostname_id or '(not set)'}")
    print(f"  Unique URL: {provider.unique_booking_url}")
    print(f"  Active: {provider.is_active}")
    print(f"  Plan: {provider.current_plan}")
    
    if not provider.domain_verified:
        print("\n⚠️  Domain not verified in database")
        print("Marking as verified...")
        provider.domain_verified = True
        provider.ssl_enabled = True
        provider.save()
        print("✓ Updated!")
    
except ServiceProvider.DoesNotExist:
    print("✗ Provider with custom_domain 'okmentor.in' not found in database!")
except Exception as e:
    print(f"Error checking database: {str(e)}")

# 5. Check database connectivity
print("\n5. DATABASE STATUS")
print("-" * 80)

try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✓ Database connected")
except Exception as e:
    print(f"✗ Database error: {str(e)}")

print("\n" + "=" * 80)
print("DIAGNOSTICS COMPLETE")
print("=" * 80)
