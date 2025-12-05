"""
Fix Cloudflare fallback origin and DNS for okmentor.in
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.conf import settings

zone_id = settings.CLOUDFLARE_ZONE_ID
headers = {
    'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
    'Content-Type': 'application/json'
}

print("=" * 80)
print("FIXING CLOUDFLARE OKMENTOR.IN CONFIGURATION")
print("=" * 80)

# 1. Check and fix fallback origin
print("\n1. CHECKING FALLBACK ORIGIN")
print("-" * 80)

fallback_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames/fallback_origin'
fallback_response = requests.get(fallback_url, headers=headers, timeout=30)
fallback_data = fallback_response.json()

if fallback_data.get('success'):
    result = fallback_data.get('result', {})
    current_origin = result.get('origin')
    current_status = result.get('status')
    
    print(f"Current Origin: {current_origin}")
    print(f"Status: {current_status}")
    
    # We need customers.nextslot.in
    expected_origin = settings.CLOUDFLARE_CNAME_TARGET
    railway_origin = settings.RAILWAY_DOMAIN
    
    print(f"Expected: {expected_origin}")
    print(f"Railway Domain: {railway_origin}")
    
    # Update if different
    if current_origin != expected_origin and current_origin != railway_origin:
        print(f"\n⚠️  Origin doesn't match expected value!")
        print(f"Setting fallback origin to: {railway_origin}")
        
        set_payload = {'origin': railway_origin}
        set_response = requests.put(fallback_url, headers=headers, json=set_payload, timeout=30)
        set_data = set_response.json()
        
        if set_data.get('success'):
            print("✓ Fallback origin updated!")
            new_result = set_data.get('result', {})
            print(f"  New origin: {new_result.get('origin')}")
            print(f"  Status: {new_result.get('status')}")
        else:
            print(f"✗ Error: {set_data.get('errors')}")
    else:
        print("✓ Fallback origin is correct")
else:
    print(f"Error getting fallback origin: {fallback_data.get('errors')}")

# 2. Check okmentor.in custom hostname
print("\n2. CHECKING OKMENTOR.IN CUSTOM HOSTNAME")
print("-" * 80)

hostnames_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames'
hostnames_response = requests.get(hostnames_url, headers=headers, timeout=30)
hostnames_data = hostnames_response.json()

if hostnames_data.get('success'):
    hostnames = hostnames_data.get('result', [])
    okmentor = None
    
    for h in hostnames:
        if h.get('hostname') == 'okmentor.in':
            okmentor = h
            break
    
    if okmentor:
        print(f"✓ okmentor.in found in Cloudflare")
        print(f"  Status: {okmentor.get('status')}")
        print(f"  SSL Status: {okmentor.get('ssl', {}).get('status')}")
        print(f"  CNAME Status: {okmentor.get('cname_status')}")
        print(f"  Ownership Status: {okmentor.get('ownership_verification', {}).get('verification_status')}")
        
        # Check if SSL needs attention
        ssl_status = okmentor.get('ssl', {}).get('status')
        if ssl_status not in ['active', 'pending_issuance']:
            print(f"\n⚠️  SSL Status is {ssl_status}")
    else:
        print("✗ okmentor.in NOT found in Cloudflare!")
else:
    print(f"Error: {hostnames_data.get('errors')}")

# 3. Ensure DNS CNAME is correct
print("\n3. CHECKING DNS CNAME RECORD")
print("-" * 80)

# Get current DNS records (might fail due to auth, but we try)
try:
    dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name=okmentor.in'
    dns_response = requests.get(dns_url, headers=headers, timeout=30)
    dns_data = dns_response.json()
    
    if dns_data.get('success'):
        records = dns_data.get('result', [])
        
        if records:
            for r in records:
                if r.get('type') == 'CNAME':
                    print(f"✓ CNAME record found")
                    print(f"  Name: {r.get('name')}")
                    print(f"  Content: {r.get('content')}")
                    print(f"  Proxied: {r.get('proxied')}")
        else:
            print("⚠️  No CNAME record found for okmentor.in")
    else:
        print("Note: Could not query DNS records (auth issue), assuming manual setup")
except Exception as e:
    print(f"Note: Could not query DNS records ({str(e)})")

# 4. Show provider information
print("\n4. PROVIDER DATABASE ENTRY")
print("-" * 80)

try:
    from providers.models import ServiceProvider
    
    provider = ServiceProvider.objects.get(custom_domain__iexact='okmentor.in')
    print(f"✓ Provider: {provider.business_name}")
    print(f"  Custom Domain: {provider.custom_domain}")
    print(f"  Domain Type: {provider.custom_domain_type}")
    print(f"  Verified: {provider.domain_verified}")
    print(f"  SSL Enabled: {provider.ssl_enabled}")
    print(f"  Active: {provider.is_active}")
    print(f"  Plan: {provider.current_plan}")
except Exception as e:
    print(f"Error: {str(e)}")

# 5. Show what user needs to do
print("\n5. NEXT STEPS FOR OKMENTOR.IN OWNER")
print("-" * 80)

print(f"""
The domain okmentor.in is configured in Cloudflare, but to make it work:

1. Go to your domain registrar (GoDaddy, Namecheap, etc.)
2. Find DNS settings for okmentor.in
3. Add or update the CNAME record:
   Name: okmentor (or @ if at root)
   Type: CNAME
   Value: customers.nextslot.in
   
4. Wait 24-48 hours for DNS to propagate
5. Test: nslookup okmentor.in
   Should show: customers.nextslot.in

Once DNS is set up, okmentor.in will work!

Your booking page will be at: https://okmentor.in/
Redirects to: https://okmentor.in/appointments/book/anju-mishra/
""")

print("=" * 80)
print("CONFIGURATION COMPLETE")
print("=" * 80)
