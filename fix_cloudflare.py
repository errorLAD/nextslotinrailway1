"""Check and configure Cloudflare Fallback Origin"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

import requests
from django.conf import settings

zone_id = settings.CLOUDFLARE_ZONE_ID
headers = {
    'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Check Fallback Origin
print('=== Checking Fallback Origin ===')
url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames/fallback_origin'
response = requests.get(url, headers=headers, timeout=30)
data = response.json()

if data.get('success'):
    result = data.get('result', {})
    print(f"Origin: {result.get('origin')}")
    print(f"Status: {result.get('status')}")
    
    if not result.get('origin'):
        print('\n⚠️  No Fallback Origin configured!')
        print('Setting fallback origin to customers.nextslot.in...')
        
        # Set fallback origin
        set_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames/fallback_origin'
        payload = {
            'origin': 'customers.nextslot.in'
        }
        set_response = requests.put(set_url, headers=headers, json=payload, timeout=30)
        set_data = set_response.json()
        
        if set_data.get('success'):
            print('✅ Fallback origin set successfully!')
        else:
            print(f"Error: {set_data.get('errors')}")
else:
    print(f"Error: {data.get('errors')}")

# Also check if customers.nextslot.in DNS record exists
print('\n=== Checking customers.nextslot.in DNS ===')
dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name=customers.nextslot.in'
dns_response = requests.get(dns_url, headers=headers, timeout=30)
dns_data = dns_response.json()

if dns_data.get('success'):
    records = dns_data.get('result', [])
    if records:
        for r in records:
            print(f"Type: {r.get('type')}, Name: {r.get('name')}, Content: {r.get('content')}, Proxied: {r.get('proxied')}")
    else:
        print('⚠️  No DNS record for customers.nextslot.in!')
        print('Creating CNAME record...')
        
        # Create the CNAME record
        create_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records'
        payload = {
            'type': 'CNAME',
            'name': 'customers',
            'content': 'web-production-200fb.up.railway.app',
            'proxied': True
        }
        create_response = requests.post(create_url, headers=headers, json=payload, timeout=30)
        create_data = create_response.json()
        
        if create_data.get('success'):
            print('✅ CNAME record created!')
        else:
            print(f"Error: {create_data.get('errors')}")
else:
    print(f"Error: {dns_data.get('errors')}")
