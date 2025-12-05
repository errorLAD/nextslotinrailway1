"""
DNS Configuration Setup for Each Service Provider's Custom Domain

This script helps configure DNS records for each provider's custom domain
to work with Cloudflare for SaaS.
"""

import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.conf import settings
from providers.models import ServiceProvider

print("=" * 80)
print("SERVICE PROVIDER DNS CONFIGURATION SETUP")
print("=" * 80)

zone_id = settings.CLOUDFLARE_ZONE_ID
headers = {
    'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Get all providers with custom domains
providers = ServiceProvider.objects.exclude(custom_domain__isnull=True).exclude(custom_domain='')

if not providers.exists():
    print("\n❌ No providers with custom domains found!")
else:
    print(f"\n✓ Found {providers.count()} provider(s) with custom domain(s)\n")
    
    for idx, provider in enumerate(providers, 1):
        print("=" * 80)
        print(f"PROVIDER {idx}: {provider.business_name}")
        print("=" * 80)
        
        domain = provider.custom_domain
        print(f"\nCustom Domain: {domain}")
        print(f"Domain Type: {provider.custom_domain_type}")
        print(f"Verified: {provider.domain_verified}")
        print(f"SSL Enabled: {provider.ssl_enabled}")
        
        # Check if it's a subdomain or external domain
        if provider.custom_domain_type == 'subdomain':
            print(f"\n✓ This is a SUBDOMAIN - No DNS changes needed!")
            print(f"  It works automatically via wildcard DNS: *.nextslot.in")
            continue
        
        # External custom domain - needs DNS setup
        print(f"\n⚠️  This is a CUSTOM DOMAIN - DNS setup required!")
        
        # Extract domain parts
        domain_parts = domain.split('.')
        if len(domain_parts) > 2:
            subdomain = domain_parts[0]  # e.g., "okmentor" from "okmentor.in"
            root_domain = '.'.join(domain_parts[1:])  # e.g., "in"
        else:
            subdomain = None
            root_domain = domain
        
        print(f"\n📋 DNS RECORDS TO ADD AT DOMAIN REGISTRAR")
        print("-" * 80)
        
        # CNAME Record
        print(f"\n1️⃣  CNAME RECORD (Main routing)")
        print(f"   Name: {'@' if not subdomain else subdomain}")
        print(f"   Type: CNAME")
        print(f"   Value: {settings.CLOUDFLARE_CNAME_TARGET}")
        print(f"   TTL: 3600")
        print(f"   Status: Proxied (Orange cloud in Cloudflare)")
        
        # Check Cloudflare for TXT records needed for SSL
        print(f"\n2️⃣  TXT RECORDS (For SSL validation - check Cloudflare)")
        
        # Get custom hostname details from Cloudflare
        try:
            hostnames_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames?hostname={domain}'
            hostnames_response = requests.get(hostnames_url, headers=headers, timeout=30)
            hostnames_data = hostnames_response.json()
            
            if hostnames_data.get('success'):
                hostnames = hostnames_data.get('result', [])
                if hostnames:
                    hostname = hostnames[0]
                    ssl_records = hostname.get('ssl', {}).get('validation_records', [])
                    
                    if ssl_records:
                        print(f"   ⚠️  Cloudflare requires these TXT records for SSL validation:\n")
                        for record in ssl_records:
                            rec_name = record.get('name', '')
                            rec_value = record.get('value', '')
                            print(f"   Name: {rec_name}")
                            print(f"   Type: TXT")
                            print(f"   Value: {rec_value}")
                            print(f"   TTL: 3600\n")
                    else:
                        print(f"   ✓ No additional TXT records needed (HTTP validation)")
        except Exception as e:
            print(f"   Note: Could not fetch Cloudflare SSL records ({str(e)})")
        
        # Provider's registrar instructions
        print(f"\n📝 STEP-BY-STEP INSTRUCTIONS FOR {provider.business_name}")
        print("-" * 80)
        print(f"""
1. Log in to your domain registrar where you own {domain}
   (e.g., GoDaddy, Namecheap, Bluehost, Hostinger, etc.)

2. Find the DNS settings/management section

3. Add the CNAME record:
   - Name: {'@' if not subdomain else subdomain}
   - Type: CNAME
   - Value: {settings.CLOUDFLARE_CNAME_TARGET}
   - TTL: 3600

4. If registrar shows SSL validation TXT records, add them too
   (Check Cloudflare dashboard for these)

5. Save the DNS changes

6. Wait 24-48 hours for DNS propagation

7. Test: nslookup {domain}
   Should show: {settings.CLOUDFLARE_CNAME_TARGET}

8. Once DNS is verified, domain will be live!
""")
        
        # Verify current DNS
        print(f"\n🔍 VERIFYING DNS RECORDS")
        print("-" * 80)
        
        dns_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={domain}'
        try:
            dns_response = requests.get(dns_url, headers=headers, timeout=30)
            dns_data = dns_response.json()
            
            if dns_data.get('success'):
                records = dns_data.get('result', [])
                if records:
                    print(f"✓ DNS records currently configured:\n")
                    for record in records:
                        print(f"  Type: {record.get('type')}")
                        print(f"  Name: {record.get('name')}")
                        print(f"  Content: {record.get('content')}")
                        print(f"  Proxied: {record.get('proxied')}\n")
                else:
                    print(f"❌ No DNS records found - Provider needs to add CNAME!")
        except Exception as e:
            print(f"Note: Could not verify DNS ({str(e)})")
        
        # Cloudflare status
        print(f"\n☁️  CLOUDFLARE STATUS")
        print("-" * 80)
        try:
            hostnames_url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames?hostname={domain}'
            hostnames_response = requests.get(hostnames_url, headers=headers, timeout=30)
            hostnames_data = hostnames_response.json()
            
            if hostnames_data.get('success'):
                hostnames = hostnames_data.get('result', [])
                if hostnames:
                    hostname = hostnames[0]
                    print(f"Status: {hostname.get('status')}")
                    print(f"SSL Status: {hostname.get('ssl', {}).get('status')}")
                    print(f"CNAME Status: {hostname.get('cname_status')}")
        except Exception as e:
            print(f"Could not fetch Cloudflare status ({str(e)})")
        
        print("\n")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
Each service provider needs to:

1. Go to their domain registrar
2. Add CNAME record pointing to: customers.nextslot.in
3. Wait 24-48 hours
4. Domain becomes live!

Once DNS is set up:
- User visits: https://okmentor.in
- Cloudflare routes to: customers.nextslot.in
- Django middleware detects: okmentor.in provider
- Shows: Provider's booking page
- URL stays: https://okmentor.in
""")

print("\n" + "=" * 80)
