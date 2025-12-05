# DigitalOcean SSL Setup Guide for Custom Domains

## Overview

This guide explains how SSL certificates work on DigitalOcean for multiple providers with custom domains.

## How SSL Provisioning Works on DigitalOcean

DigitalOcean App Platform uses **Let's Encrypt** to automatically provision SSL certificates for:
1. The main DigitalOcean app domain (e.g., `app.ondigitalocean.app`)
2. All provider subdomains (e.g., `okmentor.nextslot.in`)
3. All provider custom domains (e.g., `okmentor.in`)

### The Certificate Chain

```
User visits: okmentor.in
         ↓
DNS resolves to: okmentor.nextslot.in
         ↓
Which CNAME resolves to: app.ondigitalocean.app
         ↓
DigitalOcean receives request
         ↓
DigitalOcean detects domain (okmentor.in) in request headers
         ↓
Let's Encrypt verifies domain ownership via ACME challenge
         ↓
SSL certificate generated for okmentor.in
         ↓
HTTPS connection established
```

## SSL Status: Why You See the Error

### Current Issue for okmentor.in

**Error Message:** "doesn't support a secure connection with HTTPS"

**Causes:**
1. **DNS not yet verified** - okmentor.in hasn't propagated yet
2. **Not in DigitalOcean app domains** - Domain not added to app settings
3. **SSL pending** - Certificate is being generated (takes 5-30 min)
4. **Wrong CNAME target** - Points to wrong subdomain

## Step-by-Step SSL Setup for Each Provider

### Step 1: Provider Adds DNS Record (5 minutes)

Provider must add CNAME record in their registrar:

```
Domain: okmentor.in
Type: CNAME
Value: okmentor.nextslot.in
TTL: 3600
```

### Step 2: Wait for DNS Propagation (5 minutes to 48 hours)

Check DNS status at: https://mxtoolbox.com/cname/okmentor.in

Expected output:
```
okmentor.in → CNAME → okmentor.nextslot.in
```

### Step 3: Add Domain to DigitalOcean App Settings

**In DigitalOcean Console:**

1. Go to: Apps → Your App → Settings
2. Click: "Edit" on Custom Domains section
3. Add: `okmentor.in`
4. Add: `www.okmentor.in` (optional)
5. Click: "Save"

DigitalOcean will:
- Verify domain ownership via DNS check
- Request SSL certificate from Let's Encrypt
- Auto-renew certificate 30 days before expiry

### Step 4: Verify Domain in App (2 minutes)

1. Wait 5-10 minutes for DigitalOcean to process
2. Visit: https://okmentor.in
3. Check for green lock icon in browser

## Manual SSL Certificate Provisioning

If SSL isn't automatically provisioned, manually trigger it:

### Option A: DigitalOcean Dashboard

1. Apps → Your App → Settings
2. Remove the domain: `okmentor.in`
3. Wait 2 minutes
4. Re-add the domain: `okmentor.in`
5. DigitalOcean will retry SSL provisioning

### Option B: Using Let's Encrypt CLI

```bash
# Install certbot (if not already installed)
pip install certbot

# Request certificate
certbot certonly --manual \
  -d okmentor.in \
  -d www.okmentor.in \
  --preferred-challenges dns

# Follow prompts for DNS verification
```

## Configuration Files

### Django Settings

File: `booking_saas/settings.py`

```python
# DigitalOcean App Platform
DIGITALOCEAN_APP_DOMAIN = 'my-booking-app.ondigitalocean.app'

# SSL Configuration
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True  # Force HTTPS

# Let's Encrypt auto-renewal settings
ACME_WELL_KNOWN_URL = '/.well-known/acme-challenge/'
CUSTOM_DOMAIN_SSL_CHECK_INTERVAL = 3600  # Check every hour
```

### Middleware Configuration

File: `providers/middleware.py`

CustomDomainMiddleware handles:
- Routing custom domains to provider booking pages
- Supporting both provider subdomains and custom domains
- Works with DigitalOcean's automatic SSL

## DNS Architecture for Multiple Providers

### For Each Provider

```
Provider's Custom Domain     CNAME    Provider's Subdomain
─────────────────────────    ──→    ────────────────────
okmentor.in                          okmentor.nextslot.in
ramesh-salon.com                     ramesh-salon.nextslot.in
john-fitness.com.au                  john-fitness.nextslot.in
```

### Centralized Setup (Once)

```
nextslot.in Domain Registrar (Your Main Domain)

Name                    Type        Value
──────────────────     ──────      ─────────────────
*.nextslot.in          CNAME       app.ondigitalocean.app
www.nextslot.in        CNAME       app.ondigitalocean.app
nextslot.in            A           203.0.113.42 (your app IP)
```

## Troubleshooting SSL Issues

### Issue 1: HTTPS Error - Connection Not Secure

**Symptoms:**
- Browser shows: "This site doesn't have HTTPS"
- Address bar shows: Plain HTTP (not HTTPS)

**Solutions:**

a) **Check DNS Propagation**
```bash
# Check if domain resolves correctly
nslookup okmentor.in
# Should return: okmentor.nextslot.in
```

b) **Verify CNAME Target**
```bash
# Check CNAME chain
nslookup okmentor.nextslot.in
# Should return: app.ondigitalocean.app
```

c) **Force HTTPS Redirect**
- Ensure `SECURE_SSL_REDIRECT = True` in settings
- Test at: `https://okmentor.in`

d) **Wait for Certificate**
- SSL can take 5-30 minutes to generate
- Check DigitalOcean dashboard for status
- Re-add domain to trigger retry

### Issue 2: Certificate Error - Name Mismatch

**Symptoms:**
- Browser warning: "Subject alternate name missing"
- Certificate is for different domain

**Solutions:**

a) **Add All Domain Variants**
In DigitalOcean App Settings, add:
- `okmentor.in`
- `www.okmentor.in`

b) **Regenerate Certificate**
1. Remove domain from DigitalOcean
2. Wait 5 minutes
3. Re-add domain

c) **Check Request Headers**
Ensure X-Forwarded-Proto is set correctly:
```python
# In settings.py
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### Issue 3: SSL Certificate Expired

**Symptoms:**
- Browser error: "Certificate expired"
- In DigitalOcean: Status shows "Expired"

**Solutions:**

a) **DigitalOcean Auto-Renewal (Automatic)**
- DigitalOcean renews 30 days before expiry
- No manual action needed

b) **Manual Renewal**
1. Go to DigitalOcean Apps console
2. Remove domain
3. Wait 5 minutes
4. Re-add domain

### Issue 4: Multiple Providers Sharing Same Domain

**Problem:** Two providers configured with same custom domain

**Solutions:**

a) **Check Database**
```bash
python manage.py shell
from providers.models import ServiceProvider
ServiceProvider.objects.filter(custom_domain='okmentor.in')
# Should return only 1 provider
```

b) **Fix Duplicate**
```python
# In Django shell
provider = ServiceProvider.objects.get(id=YOUR_PROVIDER_ID)
provider.custom_domain = 'corrected-domain.com'
provider.save()
```

## Certificate Renewal Timeline

Let's Encrypt certificates are valid for **90 days**.

```
Day 0:       Certificate issued
Day 60:      DigitalOcean begins renewal process
Day 81:      Certificate renewal triggered
Day 87:      New certificate installed
Day 90:      Old certificate expires (already replaced)
```

**No action needed** - DigitalOcean handles renewal automatically.

## Provider Setup Instructions

Create these instructions for each provider:

### For Provider (okmentor.in)

1. **Provider's Registrar (GoDaddy, Namecheap, etc.)**
   ```
   Add CNAME Record:
   Name/Host:  @ (or leave blank)
   Type:       CNAME
   Value:      okmentor.nextslot.in
   TTL:        3600
   ```

2. **Wait for DNS Propagation** (5-48 hours)
   - Check at: https://mxtoolbox.com/cname/okmentor.in

3. **Visit Your Booking Page**
   - URL: https://okmentor.in
   - Should show green lock and your booking page

4. **SSL Certificate Auto-Generated**
   - Takes 5-30 minutes after DNS propagates
   - Let's Encrypt handles everything

## Monitoring SSL Status

### Check Certificate Validity

```bash
# Check certificate expiry
echo | openssl s_client -servername okmentor.in -connect okmentor.in:443 2>/dev/null | openssl x509 -noout -dates

# Output should show:
# notBefore=Jan  1 00:00:00 2024 GMT
# notAfter=Apr  1 00:00:00 2024 GMT
```

### Monitor in Django

Create management command to check SSL status:

```python
# providers/management/commands/check_ssl_status.py
from django.core.management.base import BaseCommand
from providers.models import ServiceProvider

class Command(BaseCommand):
    def handle(self, *args, **options):
        providers = ServiceProvider.objects.filter(
            custom_domain__isnull=False,
            is_active=True
        )
        
        for provider in providers:
            print(f"{provider.business_name}: {provider.custom_domain}")
            print(f"  Verified: {provider.domain_verified}")
            print(f"  SSL Enabled: {provider.ssl_enabled}")
```

## Deployment Checklist

Before going live with custom domains:

- [ ] DigitalOcean App Platform deployed
- [ ] DIGITALOCEAN_APP_DOMAIN set in settings
- [ ] Wildcard DNS configured for nextslot.in
- [ ] SECURE_SSL_REDIRECT enabled
- [ ] CustomDomainMiddleware enabled
- [ ] Provider subdomains created in DNS
- [ ] Each provider adds their CNAME record
- [ ] DNS propagates (wait 5-48 hours)
- [ ] Test with browser: https://provider.customdomain.com
- [ ] SSL certificate visible in browser
- [ ] Email notifications set up (optional)

## Support Resources

- DigitalOcean Docs: https://docs.digitalocean.com/products/app-platform/
- DNS Check Tool: https://mxtoolbox.com/cname/
- SSL Test: https://www.ssllabs.com/ssltest/
- Let's Encrypt: https://letsencrypt.org/

## Quick Reference

| Item | Value | Example |
|------|-------|---------|
| Hosting | DigitalOcean App Platform | app.ondigitalocean.app |
| SSL Provider | Let's Encrypt | Automatic, Free |
| SSL Validity | 90 days | Auto-renews at day 60 |
| TTL | 3600 seconds | 1 hour |
| DNS Propagation | 5 min to 48 hours | Usually 15-30 min |
| Provider CNAME | provider.nextslot.in | okmentor.nextslot.in |
| Main domain CNAME | *.nextslot.in | Points to app domain |

## Emergency SSL Fix

If SSL stops working suddenly:

1. **Verify DNS is correct**
   ```bash
   nslookup yourdomain.com
   ```

2. **Check DigitalOcean app is running**
   - Go to Apps dashboard
   - Check app status (should be "Running")

3. **Re-add domain to DigitalOcean**
   - Remove from custom domains
   - Wait 5 minutes
   - Re-add to trigger cert renewal

4. **Clear browser cache**
   - Ctrl+Shift+Delete
   - Clear site data for the domain

5. **Test in incognito mode**
   - Ctrl+Shift+N
   - Visit: https://yourdomain.com

## More Help

Contact support or check:
- DigitalOcean Help: https://docs.digitalocean.com/support/
- Let's Encrypt Community: https://community.letsencrypt.org/
