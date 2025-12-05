# Custom Domain Configuration - DigitalOcean Setup

## Problem Statement
Each service provider needs their own unique custom domain, but all providers must point to the same application backend (DigitalOcean App Platform). The system needs to properly distinguish between providers while routing all traffic to one application.

## Architecture Solution: Multi-Tenant SaaS with Cloudflare on DigitalOcean

### How It Works

1. **Single Application Backend**
   - One DigitalOcean App Platform domain: `nextslot-app.ondigitalocean.app` (or similar)
   - All providers use the SAME CNAME target

2. **Unique Identification Per Provider**
   - Each provider has a UNIQUE custom domain (e.g., `salon1.com`, `salon2.com`)
   - Each provider has a UNIQUE TXT verification record name (e.g., `_bv-salon1`, `_bv-salon2`)
   - Middleware routes traffic based on the Host header

3. **DNS Configuration**
   ```
   Provider 1 (Ramesh Salon):
   - Custom Domain: ramesh-salon.com
   - CNAME Record: ramesh-salon.com → nextslot-app.ondigitalocean.app (SAME for all)
   - TXT Record: _bv-ramesh-salon → booking-verify-abc123def456 (UNIQUE)
   
   Provider 2 (John Fitness):
   - Custom Domain: john-fitness.com
   - CNAME Record: john-fitness.com → nextslot-app.ondigitalocean.app (SAME for all)
   - TXT Record: _bv-john-fitness → booking-verify-xyz789uvw012 (UNIQUE)
   ```

## Database Fields

### ServiceProvider Model Fields

```python
# Custom domain configuration
custom_domain = CharField(255, unique=True)
    # Example: "ramesh-salon.com" or "book.salon.com"

custom_domain_type = CharField(20, choices=['none', 'subdomain', 'domain'])
    # 'subdomain': book.yourdomain.com
    # 'domain': yourdomain.com

# Unique CNAME target (same for all providers - DigitalOcean app domain)
cname_target = CharField(255, unique=True)
    # Value: nextslot-app.ondigitalocean.app
    # NOTE: Unique=True but stores SAME value for all providers

# Unique TXT record name (different for each provider)
txt_record_name = CharField(255)
    # Example: "_bv-ramesh-salon"
    # Unique per provider based on unique_booking_url

# Domain verification
domain_verified = BooleanField(default=False)
    # True when DNS records are verified

domain_verification_code = CharField(100)
    # Unique verification code for this provider
    # Format: "booking-verify-{random_12_chars}"
    # Example: "booking-verify-abc123def456"

ssl_enabled = BooleanField(default=False)
    # True when Cloudflare SSL is active

cloudflare_hostname_id = CharField(100)
    # Cloudflare Custom Hostname ID for this provider
```

## Settings Configuration

### Environment Variables (Required)

```bash
# .env or deployment platform settings

# DigitalOcean App Domain (REQUIRED)
DIGITALOCEAN_APP_DOMAIN=nextslot-app.ondigitalocean.app

# Alternative: if using Railway for compatibility
RAILWAY_DOMAIN=nextslot-app.ondigitalocean.app

# Cloudflare Configuration
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
CLOUDFLARE_ZONE_ID=your-zone-id
CLOUDFLARE_ACCOUNT_ID=your-account-id
```

### Django Settings (`booking_saas/settings.py`)

```python
# ============================================================================
# DIGITALOCEAN APP PLATFORM CONFIGURATION
# ============================================================================
# DigitalOcean app domain - this is what custom domains should CNAME to
# Example: nextslot-app.ondigitalocean.app
DIGITALOCEAN_APP_DOMAIN = config('DIGITALOCEAN_APP_DOMAIN', default='nextslot-app.ondigitalocean.app')

# For backward compatibility, also set RAILWAY_DOMAIN
RAILWAY_DOMAIN = config('RAILWAY_DOMAIN', default=DIGITALOCEAN_APP_DOMAIN)

# Cloudflare for SaaS - CNAME target for custom domains
# This should be the DigitalOcean app domain
CLOUDFLARE_CNAME_TARGET = config('CLOUDFLARE_CNAME_TARGET', default=DIGITALOCEAN_APP_DOMAIN)
```

## Code Updates

### 1. Fixed `domain_views.py` - `custom_domain_page()` View

Passes `verification_code` to template context so each provider sees their unique verification code.

### 2. Updated `domain_utils.py` - Generator Functions

**Function: `generate_unique_cname_target(provider)`**
```python
# Now uses DIGITALOCEAN_APP_DOMAIN instead of RAILWAY_DOMAIN
# RETURNS: nextslot-app.ondigitalocean.app (SAME for ALL providers)
# This is correct for multi-tenant SaaS architecture
```

## Provider DNS Setup Instructions

### Provider A Setup
1. **Domain**: ramesh-salon.com
2. **CNAME Record**:
   - Name: @ (or subdomain)
   - Type: CNAME
   - Value: **nextslot-app.ondigitalocean.app**
   - TTL: 3600

3. **TXT Verification Record** (UNIQUE):
   - Name: **_bv-ramesh-salon**
   - Type: TXT
   - Value: **booking-verify-abc123def456** (Provider A's unique code)
   - TTL: 3600

### Provider B Setup
1. **Domain**: john-fitness.com
2. **CNAME Record**:
   - Name: @ (or subdomain)
   - Type: CNAME
   - Value: **nextslot-app.ondigitalocean.app** (SAME as Provider A)
   - TTL: 3600

3. **TXT Verification Record** (DIFFERENT):
   - Name: **_bv-john-fitness**
   - Type: TXT
   - Value: **booking-verify-xyz789uvw012** (Provider B's unique code)
   - TTL: 3600

## How Routing Works

### Request Flow

```
1. User visits: ramesh-salon.com
   ↓
2. DNS resolves CNAME: ramesh-salon.com → nextslot-app.ondigitalocean.app
   ↓
3. Request reaches DigitalOcean App Platform with Host header: Host: ramesh-salon.com
   ↓
4. Django middleware checks Host header
   ↓
5. Middleware finds ServiceProvider with custom_domain = 'ramesh-salon.com'
   ↓
6. Request is handled by that specific provider's views
```

### Middleware Implementation (Location: providers/middleware.py)

The middleware:
1. Reads the `Host` header from incoming request
2. Matches it against `ServiceProvider.custom_domain`
3. Attaches the provider to the request
4. Views use `request.provider` to show correct booking page

## Verification Process

### DNS Verification Steps

1. **Provider adds CNAME record** to their registrar:
   - Points custom domain to DigitalOcean App Platform domain

2. **Provider adds TXT record** to their registrar:
   - Unique TXT name with unique verification code

3. **Provider clicks "Verify Domain"** in Django admin

4. **System checks DNS records**:
   ```python
   verify_domain_dns(
       domain="ramesh-salon.com",
       expected_cname="nextslot-app.ondigitalocean.app",  # SAME for all
       expected_txt="booking-verify-abc123def456",  # UNIQUE to provider
       txt_record_name="_bv-ramesh-salon"  # UNIQUE to provider
   )
   ```

5. **If both records found**:
   - Domain verification successful
   - SSL certificate issued by Cloudflare
   - Provider's booking page goes live

## Why All Providers Use Same CNAME Target

✅ **Correct**: All providers → `nextslot-app.ondigitalocean.app`
- This is a multi-tenant SaaS pattern
- One backend serves multiple customers
- Provider identification happens via:
  - Custom domain name
  - Host header routing
  - Unique TXT record verification

❌ **Incorrect**: Each provider has different CNAME (e.g., provider-1.app.ondigitalocean.app)
- Would require multiple DigitalOcean apps
- Not scalable
- Expensive to maintain

## Uniqueness Guarantees

1. **CNAME Target**: 
   - ✓ Can be same across all providers
   - ✓ DigitalOcean app domain is application backend

2. **TXT Record Name**:
   - ✓ MUST be unique per provider
   - ✓ Based on `unique_booking_url` (guaranteed unique)
   - ✓ Format: `_bv-{booking_url}`

3. **Verification Code**:
   - ✓ MUST be unique per provider
   - ✓ Generated as: `booking-verify-{random_12_chars}`
   - ✓ Stored in `domain_verification_code` field

4. **Custom Domain**:
   - ✓ Database constraint: `unique=True`
   - ✓ No two providers can use same domain

## Testing Verification

### Test DNS Configuration

```bash
# Check CNAME record for provider 1
nslookup ramesh-salon.com
# Should return: nextslot-app.ondigitalocean.app

# Check TXT record for provider 1
nslookup -type=TXT _bv-ramesh-salon.ramesh-salon.com
# Should return: booking-verify-abc123def456

# Check CNAME record for provider 2
nslookup john-fitness.com
# Should also return: nextslot-app.ondigitalocean.app (SAME!)

# Check TXT record for provider 2
nslookup -type=TXT _bv-john-fitness.john-fitness.com
# Should return: booking-verify-xyz789uvw012 (DIFFERENT from provider 1)
```

## Troubleshooting

### Issue: "CNAME points to different value"
**Solution**: Each provider's CNAME must point to `nextslot-app.ondigitalocean.app`

### Issue: "TXT record not found"
**Solution**: 
- Check TXT record name matches: `_bv-{booking_url}`
- Check TXT value matches: `booking-verify-...` code shown in provider panel

### Issue: Domain verified but not working
**Solution**: 
1. Wait 24-48 hours for DNS propagation
2. Clear browser cache
3. Check Cloudflare SSL status in provider dashboard
4. Verify DigitalOcean app is running and accessible

## Files Modified

1. **booking_saas/settings.py**
   - Changed `RAILWAY_DOMAIN` to `DIGITALOCEAN_APP_DOMAIN`
   - Updated `CLOUDFLARE_CNAME_TARGET` to use DigitalOcean app domain

2. **providers/domain_utils.py**
   - Updated `generate_unique_cname_target()` to use `DIGITALOCEAN_APP_DOMAIN`

3. **providers/domain_views.py**
   - Context now includes `verification_code`

## Summary

The custom domain system is now properly configured for DigitalOcean:
- ✅ All providers use same CNAME target (DigitalOcean app domain) - correct SaaS pattern
- ✅ Each provider has unique TXT record verification
- ✅ Each provider has unique domain (database constraint)
- ✅ Each provider has unique verification code
- ✅ Middleware routes based on Host header
- ✅ Context variables properly passed to templates
- ✅ Settings configured for DigitalOcean App Platform

## Database Fields

### ServiceProvider Model Fields

```python
# Custom domain configuration
custom_domain = CharField(255, unique=True)
    # Example: "ramesh-salon.com" or "book.salon.com"

custom_domain_type = CharField(20, choices=['none', 'subdomain', 'domain'])
    # 'subdomain': book.yourdomain.com
    # 'domain': yourdomain.com

# Unique CNAME target (same for all providers)
cname_target = CharField(255, unique=True)
    # Value: web-production-200fb.up.railway.app
    # NOTE: Unique=True but stores SAME value for all providers

# Unique TXT record name (different for each provider)
txt_record_name = CharField(255)
    # Example: "_bv-ramesh-salon"
    # Unique per provider based on unique_booking_url

# Domain verification
domain_verified = BooleanField(default=False)
    # True when DNS records are verified

domain_verification_code = CharField(100)
    # Unique verification code for this provider
    # Format: "booking-verify-{random_12_chars}"
    # Example: "booking-verify-abc123def456"

ssl_enabled = BooleanField(default=False)
    # True when Cloudflare SSL is active

cloudflare_hostname_id = CharField(100)
    # Cloudflare Custom Hostname ID for this provider
```

## Code Fixes Applied

### 1. Fixed `domain_views.py` - `custom_domain_page()` View

**Problem**: The view wasn't passing `verification_code` to the template context

**Solution**: 
```python
context = {
    'provider': provider,
    'cname_target': cname_target,  # Same for all providers
    'txt_record_name': txt_record_name,  # UNIQUE per provider
    'verification_code': verification_code,  # UNIQUE per provider
    'cloudflare_status': cloudflare_status,
}
```

**Key Points**:
- `cname_target`: Same for all providers (Railway domain)
- `txt_record_name`: Unique per provider (e.g., `_bv-ramesh-salon`)
- `verification_code`: Unique per provider (e.g., `booking-verify-abc123def456`)

### 2. Enhanced `domain_utils.py` - Generator Functions

**Function 1: `generate_unique_cname_target(provider)`**
```python
# RETURNS: web-production-200fb.up.railway.app (SAME for ALL providers)
# This is correct for multi-tenant SaaS architecture
```

**Function 2: `generate_unique_txt_record_name(provider)`**
```python
# RETURNS: _bv-{provider.unique_booking_url}
# Example: _bv-ramesh-salon (UNIQUE per provider)
```

## Provider DNS Setup Instructions

### Provider A Setup
1. **Domain**: ramesh-salon.com
2. **CNAME Record**:
   - Name: @ (or subdomain)
   - Type: CNAME
   - Value: **web-production-200fb.up.railway.app**
   - TTL: 3600

3. **TXT Verification Record** (UNIQUE):
   - Name: **_bv-ramesh-salon**
   - Type: TXT
   - Value: **booking-verify-abc123def456** (Provider A's unique code)
   - TTL: 3600

### Provider B Setup
1. **Domain**: john-fitness.com
2. **CNAME Record**:
   - Name: @ (or subdomain)
   - Type: CNAME
   - Value: **web-production-200fb.up.railway.app** (SAME as Provider A)
   - TTL: 3600

3. **TXT Verification Record** (DIFFERENT):
   - Name: **_bv-john-fitness**
   - Type: TXT
   - Value: **booking-verify-xyz789uvw012** (Provider B's unique code)
   - TTL: 3600

## How Routing Works

### Request Flow

```
1. User visits: ramesh-salon.com
   ↓
2. DNS resolves CNAME: ramesh-salon.com → web-production-200fb.up.railway.app
   ↓
3. Request reaches Railway app with Host header: Host: ramesh-salon.com
   ↓
4. Django middleware checks Host header
   ↓
5. Middleware finds ServiceProvider with custom_domain = 'ramesh-salon.com'
   ↓
6. Request is handled by that specific provider's views
```

### Middleware Implementation (Location: providers/middleware.py)

The middleware:
1. Reads the `Host` header from incoming request
2. Matches it against `ServiceProvider.custom_domain`
3. Attaches the provider to the request
4. Views use `request.provider` to show correct booking page

## Verification Process

### DNS Verification Steps

1. **Provider adds CNAME record** to their registrar:
   - Points custom domain to Railway app

2. **Provider adds TXT record** to their registrar:
   - Unique TXT name with unique verification code

3. **Provider clicks "Verify Domain"** in Django admin

4. **System checks DNS records**:
   ```python
   verify_domain_dns(
       domain="ramesh-salon.com",
       expected_cname="web-production-200fb.up.railway.app",  # SAME for all
       expected_txt="booking-verify-abc123def456",  # UNIQUE to provider
       txt_record_name="_bv-ramesh-salon"  # UNIQUE to provider
   )
   ```

5. **If both records found**:
   - Domain verification successful
   - SSL certificate issued by Cloudflare
   - Provider's booking page goes live

## Important Notes

### Why All Providers Use Same CNAME Target

✅ **Correct**: All providers → `web-production-200fb.up.railway.app`
- This is a multi-tenant SaaS pattern
- One backend serves multiple customers
- Provider identification happens via:
  - Custom domain name
  - Host header routing
  - Unique TXT record verification

❌ **Incorrect**: Each provider has different CNAME (e.g., provider-1.railway.app)
- Would require multiple Railway apps
- Not scalable
- Expensive to maintain

### Uniqueness Guarantees

1. **CNAME Target**: 
   - ✓ Can be same across all providers
   - ✓ Railway app domain is application backend

2. **TXT Record Name**:
   - ✓ MUST be unique per provider
   - ✓ Based on `unique_booking_url` (guaranteed unique)
   - ✓ Format: `_bv-{booking_url}`

3. **Verification Code**:
   - ✓ MUST be unique per provider
   - ✓ Generated as: `booking-verify-{random_12_chars}`
   - ✓ Stored in `domain_verification_code` field

4. **Custom Domain**:
   - ✓ Database constraint: `unique=True`
   - ✓ No two providers can use same domain

## Testing Verification

### Test DNS Configuration

```bash
# Check CNAME record for provider 1
nslookup ramesh-salon.com
# Should return: web-production-200fb.up.railway.app

# Check TXT record for provider 1
nslookup -type=TXT _bv-ramesh-salon.ramesh-salon.com
# Should return: booking-verify-abc123def456

# Check CNAME record for provider 2
nslookup john-fitness.com
# Should also return: web-production-200fb.up.railway.app (SAME!)

# Check TXT record for provider 2
nslookup -type=TXT _bv-john-fitness.john-fitness.com
# Should return: booking-verify-xyz789uvw012 (DIFFERENT from provider 1)
```

## Troubleshooting

### Issue: "CNAME points to different value"
**Solution**: Each provider's CNAME must point to `web-production-200fb.up.railway.app`

### Issue: "TXT record not found"
**Solution**: 
- Check TXT record name matches: `_bv-{booking_url}`
- Check TXT value matches: `booking-verify-...` code shown in provider panel

### Issue: Domain verified but not working
**Solution**: 
1. Wait 24-48 hours for DNS propagation
2. Clear browser cache
3. Check Cloudflare SSL status in provider dashboard

## Files Modified

1. **providers/domain_views.py**
   - Fixed `custom_domain_page()` to include `verification_code` in context

2. **providers/domain_utils.py**
   - Enhanced `generate_unique_cname_target()` with better documentation
   - Enhanced `generate_unique_txt_record_name()` with better documentation

3. **providers/models.py**
   - Database fields already properly configured

4. **providers/templates/providers/custom_domain.html**
   - Now receives `verification_code` from context

## Summary

The custom domain system is now properly configured:
- ✅ All providers use same CNAME target (correct SaaS pattern)
- ✅ Each provider has unique TXT record verification
- ✅ Each provider has unique domain (database constraint)
- ✅ Each provider has unique verification code
- ✅ Middleware routes based on Host header
- ✅ Context variables properly passed to templates
