# Multi-Domain Configuration for Service Providers

## Overview
Each service provider can have their own unique custom domain. The system supports two types of domains:

1. **Subdomains**: `salon.nextslot.in` (instant, auto-verified)
2. **Custom Domains**: `yourdomain.com` (requires DNS configuration)

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Incoming Request                         │
│                   Host: okmentor.in                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           CustomDomainMiddleware (providers)                │
│  - Detects custom domain                                    │
│  - Finds provider by custom_domain field                    │
│  - Sets request.custom_domain_provider                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│        Routes to Provider's Booking Page                    │
│   URL: /appointments/book/{unique_booking_url}/             │
│   But served from custom domain                             │
└─────────────────────────────────────────────────────────────┘
```

### Current Configuration

**Settings** (`booking_saas/settings.py`):
- `DEFAULT_DOMAIN = 'nextslot.in'` - Main application domain
- `CLOUDFLARE_CNAME_TARGET = 'customers.nextslot.in'` - Fallback for custom domains
- `ALLOWED_HOSTS = '*'` - Accept all hosts, validate in middleware

**Middleware** (registered in MIDDLEWARE):
```python
'providers.middleware.CustomDomainMiddleware'  # Handles domain routing
```

**Cloudflare Settings** (`.env`):
```
CLOUDFLARE_API_TOKEN=puSudOl4GhSRBKBjrf2msXWpJWI2C6-H7udLu__g
CLOUDFLARE_ZONE_ID=1f83e1172faca4c46586f82a9453c945
CLOUDFLARE_CNAME_TARGET=customers.nextslot.in
```

---

## How Each Provider Gets Their Domain

### For PRO Plan Users Only

#### Option 1: Subdomain (Recommended for Quick Setup)
- **What**: `customername.nextslot.in`
- **Setup Time**: Instant (no DNS required)
- **SSL**: Auto-configured
- **How**:
  1. Provider goes to **Dashboard → Custom Domain**
  2. Chooses "Use Subdomain"
  3. Enters desired subdomain name
  4. **Done!** Domain is live immediately

#### Option 2: Custom Domain (For Brand Identity)
- **What**: `yourdomain.com` or `book.yourdomain.com`
- **Setup Time**: 24-48 hours (DNS propagation)
- **SSL**: Auto-configured by Cloudflare
- **How**:
  1. Provider goes to **Dashboard → Custom Domain**
  2. Chooses "Use Custom Domain"
  3. Enters their domain (must own it)
  4. Adds CNAME record to their DNS registrar:
     ```
     Name: (subdomain or @)
     Type: CNAME
     Value: customers.nextslot.in
     ```
  5. Verifies ownership
  6. Wait for DNS propagation (24-48 hours)

---

## Database Schema

### ServiceProvider Model Fields

```python
# Custom domain fields
custom_domain = CharField(max_length=255, blank=True)
# Examples: "okmentor.in", "salon.nextslot.in"

custom_domain_type = CharField(
    choices=['none', 'subdomain', 'domain'],
    default='none'
)

domain_verified = BooleanField(default=False)
# True when DNS records are verified

domain_verification_code = CharField(max_length=255, blank=True)
# Unique code for verification

ssl_enabled = BooleanField(default=False)
# True when SSL certificate is active

cloudflare_hostname_id = CharField(max_length=255, blank=True)
# Cloudflare's hostname ID for management

cname_target = CharField(max_length=255, blank=True)
# CNAME target (usually customers.nextslot.in)

txt_record_name = CharField(max_length=255, blank=True)
# TXT record name for verification

plan_end_date = DateField(null=True, blank=True)
# PRO plan expiry date
```

---

## Flow: How Requests Are Routed

### Step 1: Request Arrives
```
GET https://okmentor.in/
Host: okmentor.in
```

### Step 2: Middleware Processing
The `CustomDomainMiddleware` checks:

```python
# 1. Is this a custom domain? (not the default domain)
check_host = 'okmentor.in'
default_domain = 'nextslot.in'

# 2. Query database for provider with this custom domain
provider = ServiceProvider.objects.get(
    custom_domain__iexact='okmentor.in',
    is_active=True
)
# Result: Finds "Anju Mishra" provider

# 3. Set request attributes
request.custom_domain_provider = provider
request.is_custom_domain = True

# 4. Redirect to provider's booking page
redirect('/appointments/book/anju-mishra/')
```

### Step 3: User Sees
- URL bar shows: `https://okmentor.in/`
- Content from: Provider's booking page
- Database shows: Provider associated with custom domain

---

## Adding Multiple Domains to a Provider

### Scenario: Provider Wants Both

```
- Subdomain: salon.nextslot.in (for quick access)
- Custom: salon.in (for brand/SEO)
```

**Current Limitation**: Each provider can have only ONE active custom domain.

**Workaround**: 
1. Configure one domain in provider's account
2. Use DNS aliases to point multiple domains:
   ```
   salon.nextslot.in → CNAME → customers.nextslot.in
   salon.in → CNAME → customers.nextslot.in
   book.salon.in → CNAME → customers.nextslot.in
   ```

---

## DNS Records Required for Each Domain

### For Subdomains (Automatic)
No DNS changes needed. System handles automatically.

### For Custom Domains

**Required DNS Records**:

```
Name: @ (or your subdomain)
Type: CNAME
Value: customers.nextslot.in
TTL: 3600

Name: _booking-verify (Optional, for verification)
Type: TXT
Value: {provider_verification_code}
TTL: 3600
```

**Example for okmentor.in:**
```
okmentor.in (A or CNAME) → customers.nextslot.in
```

---

## Troubleshooting

### Issue: Domain appears in list but not working

**Cause**: DNS not propagated or CNAME not correct

**Solution**:
```bash
# Check DNS records
nslookup okmentor.in
# Should show: customers.nextslot.in

# Verify Cloudflare
curl -H "Authorization: Bearer {TOKEN}" \
  https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/custom_hostnames
# Should show hostname with status: "active"
```

### Issue: Provider can't add custom domain

**Cause**: Not on PRO plan or already has active domain

**Solution**:
1. Check: `provider.current_plan == 'pro'`
2. Check: `provider.domain_verified == False`
3. Run: `provider.downgrade_to_free()` to reset

### Issue: Multiple providers have same domain

**Prevent**: Database constraint in migration

```python
# Check for duplicates
from providers.models import ServiceProvider
duplicates = ServiceProvider.objects.values('custom_domain')\
    .annotate(count=Count('id'))\
    .filter(count__gt=1)
```

---

## Configuration Checklist

- [x] `MIDDLEWARE` includes `CustomDomainMiddleware`
- [x] `ALLOWED_HOSTS = '*'` to accept any domain
- [x] `.env` has Cloudflare credentials
- [x] `DEFAULT_DOMAIN` set to `nextslot.in`
- [x] `CLOUDFLARE_CNAME_TARGET` set to `customers.nextslot.in`
- [x] Database fields created (custom_domain, domain_verified, etc.)
- [x] Provider model has `has_pro_features()` method
- [ ] Frontend UI for domain management
- [ ] Admin interface for domain verification
- [ ] Email notifications for DNS verification

---

## Testing Multi-Domain Setup

### Test 1: Subdomain Works

```bash
# Add subdomain via admin
python manage.py shell
from providers.models import ServiceProvider
provider = ServiceProvider.objects.first()
provider.custom_domain = 'testsalon.nextslot.in'
provider.custom_domain_type = 'subdomain'
provider.domain_verified = True
provider.save()

# Test access (requires DNS or hosts file entry)
curl -H "Host: testsalon.nextslot.in" http://localhost:8000/
```

### Test 2: Custom Domain Works

```bash
# Add custom domain
provider.custom_domain = 'salon.in'
provider.custom_domain_type = 'domain'
provider.domain_verified = True
provider.save()

# Test with hosts file entry
curl -H "Host: salon.in" http://localhost:8000/
```

### Test 3: Cloudflare Integration

```bash
python fix_cloudflare.py
python test_cloudflare.py
```

---

## Performance Considerations

### Middleware Check Optimization

The middleware does:
1. Check if host matches custom domain
2. Query database for provider
3. Redirect if at root path

**Performance Impact**: ~10ms per request (one DB query)

**Optimization**: Add caching layer
```python
from django.views.decorators.cache import cache_page

# Cache for 1 hour
@cache_page(3600)
def get_provider_by_domain(domain):
    return ServiceProvider.objects.get(custom_domain=domain)
```

---

## Next Steps

1. **Test Custom Domain Setup**: Try adding a provider with custom domain
2. **Verify Cloudflare**: Run `python test_cloudflare.py`
3. **DNS Configuration**: Set up CNAME records for okmentor.in
4. **Domain Verification**: Implement verification endpoint
5. **Frontend Updates**: Add domain management UI to provider dashboard

---

## Related Files

- `providers/middleware.py` - CustomDomainMiddleware
- `providers/domain_views.py` - Domain management views
- `providers/domain_utils.py` - Domain utilities
- `providers/cloudflare_saas.py` - Cloudflare API integration
- `providers/models.py` - ServiceProvider model
- `booking_saas/settings.py` - Django settings

