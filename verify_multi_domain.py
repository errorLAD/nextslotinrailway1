"""
Verify multi-domain configuration for all service providers.
Shows each provider's custom domain status.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from providers.models import ServiceProvider
from django.conf import settings

print("=" * 80)
print("MULTI-DOMAIN CONFIGURATION VERIFICATION")
print("=" * 80)

# 1. Check system settings
print("\n1. SYSTEM CONFIGURATION")
print("-" * 80)
print(f"Default Domain: {settings.DEFAULT_DOMAIN}")
print(f"Railway Domain: {settings.RAILWAY_DOMAIN}")
print(f"Cloudflare CNAME Target: {settings.CLOUDFLARE_CNAME_TARGET}")
print(f"Cloudflare Zone ID: {settings.CLOUDFLARE_ZONE_ID[:20]}..." if settings.CLOUDFLARE_ZONE_ID else "NOT SET")
print(f"Allowed Hosts: {settings.ALLOWED_HOSTS}")

# 2. Check middleware
print("\n2. MIDDLEWARE CONFIGURATION")
print("-" * 80)
has_custom_domain_middleware = any('CustomDomainMiddleware' in m for m in settings.MIDDLEWARE)
print(f"CustomDomainMiddleware Enabled: {'✓' if has_custom_domain_middleware else '✗'}")

# 3. Check all providers
print("\n3. SERVICE PROVIDERS - CUSTOM DOMAIN STATUS")
print("-" * 80)

providers = ServiceProvider.objects.all()

if not providers.exists():
    print("No service providers found.")
else:
    print(f"Total Providers: {providers.count()}\n")
    
    pro_count = 0
    custom_domain_count = 0
    verified_count = 0
    
    for provider in providers:
        status = "✓" if provider.is_active else "✗"
        plan = "PRO" if provider.has_pro_features() else "FREE"
        
        print(f"{status} {provider.business_name}")
        print(f"   Plan: {plan}")
        
        if provider.custom_domain:
            print(f"   Domain: {provider.custom_domain}")
            print(f"   Type: {provider.custom_domain_type}")
            print(f"   Verified: {'✓' if provider.domain_verified else '✗'}")
            print(f"   SSL: {'✓' if provider.ssl_enabled else '✗'}")
            custom_domain_count += 1
            if provider.domain_verified:
                verified_count += 1
        else:
            print(f"   Domain: (none configured)")
        
        if provider.has_pro_features():
            pro_count += 1
        
        print()
    
    print(f"Summary:")
    print(f"  PRO Users: {pro_count}/{providers.count()}")
    print(f"  With Custom Domains: {custom_domain_count}/{providers.count()}")
    print(f"  Verified Domains: {verified_count}/{custom_domain_count}" if custom_domain_count > 0 else "  No domains configured")

# 4. Show how to add a custom domain
print("\n4. HOW TO ADD A CUSTOM DOMAIN")
print("-" * 80)
print("""
For each provider (PRO plan only):

Option A - Subdomain (Instant):
  provider.custom_domain = 'customername.nextslot.in'
  provider.custom_domain_type = 'subdomain'
  provider.domain_verified = True
  provider.save()

Option B - Custom Domain (24-48 hours):
  provider.custom_domain = 'yourdomain.com'
  provider.custom_domain_type = 'domain'
  provider.domain_verified = False  # Requires DNS verification
  provider.save()

Then the provider must add CNAME DNS record:
  Name: @ (or subdomain)
  Type: CNAME
  Value: customers.nextslot.in
""")

# 5. Test connectivity
print("\n5. CLOUDFLARE CONNECTIVITY TEST")
print("-" * 80)

if settings.CLOUDFLARE_API_TOKEN:
    import requests
    
    headers = {
        'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        url = f'https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}'
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if data.get('success'):
            print("✓ Cloudflare API: CONNECTED")
            zone = data.get('result', {})
            print(f"  Zone: {zone.get('name')} ({zone.get('status')})")
        else:
            print("✗ Cloudflare API: FAILED")
            print(f"  Error: {data.get('errors')}")
    except Exception as e:
        print(f"✗ Cloudflare API: ERROR ({str(e)})")
else:
    print("⚠ Cloudflare credentials not configured")

print("\n" + "=" * 80)
