# Unique CNAME Per Provider - Complete Configuration Guide

## Overview

Each service provider now gets their own UNIQUE CNAME target (subdomain) instead of sharing a single `customers.nextslot.in` domain.

## Architecture

### Provider Subdomain Model

```
Provider 1: Ramesh Salon
├── Unique Booking URL: ramesh-salon
├── Provider Subdomain: ramesh-salon.nextslot.in
├── Custom Domain: ramesh-salon.com (or any domain they own)
├── DNS Setup:
│   ├── ramesh-salon.com CNAME → ramesh-salon.nextslot.in ✓ (Provider sets this)
│   └── ramesh-salon.nextslot.in CNAME → nextslot-app.ondigitalocean.app ✓ (We configure)
└── DNS Resolution:
    1. User visits: ramesh-salon.com
    2. Resolves to: ramesh-salon.nextslot.in (via provider's CNAME)
    3. Resolves to: nextslot-app.ondigitalocean.app (via Cloudflare)
    4. Hits DigitalOcean app with Host: ramesh-salon.com
    5. Middleware identifies provider

Provider 2: John Fitness
├── Unique Booking URL: john-fitness
├── Provider Subdomain: john-fitness.nextslot.in
├── Custom Domain: john-fitness.com
├── DNS Setup:
│   ├── john-fitness.com CNAME → john-fitness.nextslot.in
│   └── john-fitness.nextslot.in CNAME → nextslot-app.ondigitalocean.app
└── DNS Resolution: [Same pattern as above]

Provider 3: OKMentor
├── Unique Booking URL: okmentor
├── Provider Subdomain: okmentor.nextslot.in
├── Custom Domain: okmentor.in
├── DNS Setup:
│   ├── okmentor.in CNAME → okmentor.nextslot.in
│   └── okmentor.nextslot.in CNAME → nextslot-app.ondigitalocean.app
└── DNS Resolution: [Same pattern as above]
```

## Configuration Steps

### 1. Django Settings (`booking_saas/settings.py`)

```python
# Base domain for provider subdomains
PROVIDER_SUBDOMAIN_BASE = config('PROVIDER_SUBDOMAIN_BASE', default='nextslot.in')

# DigitalOcean App Platform
DIGITALOCEAN_APP_DOMAIN = config('DIGITALOCEAN_APP_DOMAIN', default='nextslot-app.ondigitalocean.app')

# Cloudflare Configuration
CLOUDFLARE_API_TOKEN = config('CLOUDFLARE_API_TOKEN', default='')
CLOUDFLARE_ZONE_ID = config('CLOUDFLARE_ZONE_ID', default='')
CLOUDFLARE_ACCOUNT_ID = config('CLOUDFLARE_ACCOUNT_ID', default='')
```

### 2. Setup Cloudflare DNS Records

Run the setup script to create CNAME records in Cloudflare:

```bash
python setup_cloudflare_dns.py
```

This script will:
1. Connect to Cloudflare API
2. For each provider, create a CNAME record:
   - Name: `{booking_url}.nextslot.in`
   - Target: `nextslot-app.ondigitalocean.app`
3. Display instructions for each provider

### 3. Each Provider's Configuration

For Provider with booking URL: `ramesh-salon`

**Their Unique Subdomain**: `ramesh-salon.nextslot.in`

**If they want to use their own domain** (e.g., `ramesh-salon.com`):

At their domain registrar, they should add:
```
Type: CNAME
Name: @ (or www, depending on setup)
Target: ramesh-salon.nextslot.in
TTL: 3600
```

**If they want to use our platform subdomain**:
They can directly use: `ramesh-salon.nextslot.in` (no CNAME needed)

## Database Schema

### ServiceProvider Fields

```python
# Unique booking URL (unique=True)
unique_booking_url = SlugField(max_length=100, unique=True)
    # Example: "ramesh-salon", "john-fitness", "okmentor"

# Custom domain (optional, if provider wants to use their own domain)
custom_domain = CharField(255, unique=True, blank=True)
    # Example: "ramesh-salon.com", "john-fitness.com", "okmentor.in"

# UNIQUE CNAME target for this provider
cname_target = CharField(255, unique=True)
    # Generated as: {unique_booking_url}.{PROVIDER_SUBDOMAIN_BASE}
    # Example: "ramesh-salon.nextslot.in"

# Unique TXT record for verification
txt_record_name = CharField(255)
    # Example: "_bv-ramesh-salon"

# Verification code (unique per provider)
domain_verification_code = CharField(100)
    # Example: "booking-verify-abc123def456"
```

## How DNS Resolution Works

### Scenario 1: Provider Using Their Own Domain (ramesh-salon.com)

```
Step 1: User visits ramesh-salon.com
  ↓
Step 2: Browser resolves ramesh-salon.com via DNS
  - Registrar returns: CNAME ramesh-salon.nextslot.in
  ↓
Step 3: Browser resolves ramesh-salon.nextslot.in via DNS
  - Cloudflare returns: CNAME nextslot-app.ondigitalocean.app
  ↓
Step 4: Browser resolves nextslot-app.ondigitalocean.app
  - DigitalOcean returns: A record 123.45.67.89 (app server IP)
  ↓
Step 5: Browser connects to 123.45.67.89
  - HTTP Request includes: Host: ramesh-salon.com (original domain)
  ↓
Step 6: DigitalOcean receives request
  - Request headers contain: Host: ramesh-salon.com
  ↓
Step 7: Django middleware processes request
  - Checks: ServiceProvider.objects.filter(custom_domain='ramesh-salon.com')
  - Finds: Ramesh Salon's provider instance
  - Attaches to request: request.provider = ramesh_salon_instance
  ↓
Step 8: Django views use request.provider
  - Shows Ramesh Salon's booking page
  ✓ Success!
```

### Scenario 2: Provider Using Platform Subdomain (ramesh-salon.nextslot.in)

```
Step 1: User visits ramesh-salon.nextslot.in
  ↓
Step 2-4: DNS resolution same as Step 3-4 above
  ↓
Step 5: Browser connects to app server
  - HTTP Request includes: Host: ramesh-salon.nextslot.in
  ↓
Step 6: Django middleware processes request
  - Checks: Custom domain first (not found)
  - Checks: Subdomain pattern "*.nextslot.in"
  - Extracts: "ramesh-salon"
  - Finds: ServiceProvider.unique_booking_url = 'ramesh-salon'
  - Attaches to request: request.provider = ramesh_salon_instance
  ↓
Step 7: Django views use request.provider
  - Shows Ramesh Salon's booking page
  ✓ Success!
```

## Code Changes

### 1. `booking_saas/settings.py`

Changed from single shared domain to provider-specific subdomains:

```python
# OLD (Single shared domain):
CLOUDFLARE_CNAME_TARGET = 'customers.nextslot.in'  # All providers point here

# NEW (Each provider gets unique subdomain):
PROVIDER_SUBDOMAIN_BASE = 'nextslot.in'  # Base for subdomains
# Each provider gets: {booking_url}.nextslot.in
```

### 2. `providers/domain_utils.py`

Updated `generate_unique_cname_target()`:

```python
def generate_unique_cname_target(provider):
    """
    Returns UNIQUE CNAME for each provider.
    
    Example outputs:
    - Provider 1: ramesh-salon.nextslot.in
    - Provider 2: john-fitness.nextslot.in
    - Provider 3: okmentor.nextslot.in
    """
    booking_url = provider.unique_booking_url
    base_domain = getattr(settings, 'PROVIDER_SUBDOMAIN_BASE', 'nextslot.in')
    unique_cname_target = f"{booking_url}.{base_domain}"
    
    provider.cname_target = unique_cname_target
    provider.save()
    return unique_cname_target
```

### 3. `setup_cloudflare_dns.py` (NEW)

New script to setup provider subdomain CNAME records in Cloudflare:

```bash
python setup_cloudflare_dns.py
```

Creates CNAME records:
- ramesh-salon.nextslot.in → nextslot-app.ondigitalocean.app
- john-fitness.nextslot.in → nextslot-app.ondigitalocean.app
- okmentor.nextslot.in → nextslot-app.ondigitalocean.app

## Provider Setup Instructions

### For Each Provider

1. **Get Your Unique Subdomain**
   - Admin shows: `ramesh-salon.nextslot.in`
   - This is YOUR unique booking domain

2. **Option A: Use Platform Subdomain**
   - Share: `ramesh-salon.nextslot.in` with customers
   - Your booking page: `https://ramesh-salon.nextslot.in/book/ramesh-salon`
   - No DNS configuration needed!

3. **Option B: Use Your Own Domain**
   - You own: `ramesh-salon.com`
   - At your domain registrar, add:
     ```
     Type: CNAME
     Name: @ (root) or www
     Target: ramesh-salon.nextslot.in
     TTL: 3600
     ```
   - Your booking page: `https://ramesh-salon.com/book/ramesh-salon`
   - After 24-48 hours, domain will be live!

## Verification

### Test DNS Resolution

```bash
# Provider 1 - Platform subdomain
nslookup ramesh-salon.nextslot.in
# Should resolve to DigitalOcean app

# Provider 1 - Custom domain
nslookup ramesh-salon.com
# Should resolve to: ramesh-salon.nextslot.in → nextslot-app.ondigitalocean.app

# Provider 2
nslookup john-fitness.nextslot.in
nslookup john-fitness.com

# Provider 3
nslookup okmentor.nextslot.in
nslookup okmentor.in
```

### Check Service Provider Configuration

```python
from providers.models import ServiceProvider

provider = ServiceProvider.objects.get(unique_booking_url='ramesh-salon')
print(f"Booking URL: {provider.unique_booking_url}")
print(f"CNAME Target: {provider.cname_target}")  # ramesh-salon.nextslot.in
print(f"Custom Domain: {provider.custom_domain}")  # ramesh-salon.com
print(f"TXT Record Name: {provider.txt_record_name}")  # _bv-ramesh-salon
print(f"Verification Code: {provider.domain_verification_code}")
```

## Benefits of This Architecture

✅ **Each provider is isolated** - Own unique subdomain  
✅ **Multiple domain options** - Use platform subdomain or custom domain  
✅ **Easy management** - Single DigitalOcean app for all  
✅ **Scalable** - Add new providers instantly  
✅ **Cost-effective** - One app, multiple customers  
✅ **Easy SSL** - Automatic HTTPS for all subdomains and custom domains  
✅ **No shared domain issues** - Each provider has their own unique subdomain  

## Troubleshooting

### Issue: Provider sees wrong booking page
**Solution**: Check middleware configuration and Host header routing

### Issue: CNAME record not updating in Cloudflare
**Solution**: Run `python setup_cloudflare_dns.py` again

### Issue: DNS not resolving
**Solution**: Wait 24-48 hours for propagation, then check:
```bash
nslookup {provider_subdomain}.nextslot.in
nslookup {custom_domain}
```

### Issue: SSL certificate not issued
**Solution**: Ensure CNAME records are properly configured

## Summary

- ✅ Each provider gets UNIQUE subdomain: `{booking_url}.nextslot.in`
- ✅ Each provider gets UNIQUE CNAME target
- ✅ Each provider gets UNIQUE TXT record verification
- ✅ Each provider gets UNIQUE verification code
- ✅ Providers can use platform subdomain OR their own domain
- ✅ All resolve to single DigitalOcean app
- ✅ Middleware routes based on Host header
- ✅ Full isolation between providers
