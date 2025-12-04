"""Check Cloudflare Custom Hostname validation records for okmentor.in"""
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

# Get custom hostname details for okmentor.in
url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames'
response = requests.get(url, headers=headers, timeout=30)
data = response.json()

if data.get('success'):
    for h in data.get('result', []):
        if h.get('hostname') == 'okmentor.in':
            print('=== okmentor.in Cloudflare Status ===')
            print(f"Status: {h.get('status')}")
            print(f"SSL Status: {h.get('ssl', {}).get('status')}")
            print()
            print('=== Ownership Verification ===')
            ov = h.get('ownership_verification', {})
            print(f"Type: {ov.get('type')}")
            print(f"Name: {ov.get('name')}")
            print(f"Value: {ov.get('value')}")
            print()
            print('=== SSL Validation Records (TXT) ===')
            ssl = h.get('ssl', {})
            recs = ssl.get('validation_records', [])
            if recs:
                for rec in recs:
                    print(f"Name: {rec.get('txt_name')}")
                    print(f"Value: {rec.get('txt_value')}")
            else:
                print('No validation records yet - may appear after CNAME is detected')
            print()
            print('=== Full SSL Object ===')
            print(ssl)
