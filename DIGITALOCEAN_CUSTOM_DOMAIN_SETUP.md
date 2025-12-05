# DigitalOcean Custom Domain Configuration Guide

## Overview

Now that your app is running on DigitalOcean PostgreSQL, here's how to configure custom domains for service providers.

---

## Architecture on DigitalOcean

```
┌─────────────────────────────────────────────────────────┐
│                  Service Providers                      │
│  - okmentor.in, salon.nextslot.in, yourdomain.com      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │   Cloudflare for SaaS      │
         │ (SSL + DNS Management)     │
         │ Fallback: customers.in     │
         └────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │  DigitalOcean App Platform  │
        │  - Django application       │
        │  - PostgreSQL database      │
        │  - Custom domain routing    │
        └──────────────┬──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   CustomDomainMiddleware      Provider Booking Pages
   - Detects domain            - anju-mishra
   - Routes to provider         - salon-owner
                               - fitness-center
```

---

## Step 1: Deploy to DigitalOcean

### Option A: Using DigitalOcean App Platform (Recommended)

1. **Create an App on DigitalOcean App Platform**
   - Go to: https://cloud.digitalocean.com/apps
   - Click "Create App"
   - Connect your GitHub repo: `errorLAD/nextslotinrailway1`
   - Select branch: `main`

2. **Configure the App**
   ```yaml
   Name: nextslot-booking-app
   Region: New York (nyc)
   
   Components:
   - Service (Web)
     - Source: GitHub
     - Repo: errorLAD/nextslotinrailway1
     - Build command: pip install -r requirements.txt && python manage.py migrate
     - Run command: gunicorn booking_saas.wsgi --bind 0.0.0.0:8080
   
   - Database: PostgreSQL (already configured)
   
   Environment Variables:
   - DEBUG=False (for production)
   - SECRET_KEY=your-secret-key
   - DATABASE_URL=postgresql://...
   - CLOUDFLARE_API_TOKEN=...
   - CLOUDFLARE_ZONE_ID=...
   ```

3. **Deploy**
   - Click "Create Resources"
   - Wait for deployment (5-10 minutes)
   - Get your app URL: `https://nextslot-xyz.ondigitalocean.app`

### Option B: Using DigitalOcean Droplet

If using a Droplet instead of App Platform:

```bash
# SSH into your Droplet
ssh root@your.droplet.ip

# Install dependencies
apt update && apt install -y python3 python3-pip postgresql-client nginx

# Clone repository
git clone https://github.com/errorLAD/nextslotinrailway1.git
cd nextslotinrailway1

# Install Python packages
pip install -r requirements.txt

# Create .env file with DigitalOcean PostgreSQL credentials
nano .env
# Add: DATABASE_URL=postgresql://doadmin:password@host:25060/defaultdb?sslmode=require

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn booking_saas.wsgi --bind 0.0.0.0:8000
```

---

## Step 2: Configure DNS on DigitalOcean

### Add Your Domain to DigitalOcean

1. **Go to Networking → Domains**
2. **Click "Add Domain"**
3. **Enter your domain** (e.g., `nextslot.in`)
4. **Point nameservers** at your registrar to:
   ```
   ns1.digitalocean.com
   ns2.digitalocean.com
   ns3.digitalocean.com
   ```

### Add DNS Records

Once domain is added to DigitalOcean:

```
# A Record (for main domain)
Name: @
Type: A
Value: your-app-ip-or-digitalocean-app-url

# CNAME for subdomains
Name: www
Type: CNAME
Value: @

# CNAME for Cloudflare fallback
Name: customers
Type: CNAME
Value: customers.nextslot.in (or your app domain)

# CNAME for custom domains fallback
Name: fallback
Type: CNAME
Value: your-app-domain.ondigitalocean.app
```

---

## Step 3: Configure Cloudflare for Custom Domains

### Enable Cloudflare for your DigitalOcean Domain

1. **Update nameservers at registrar** to Cloudflare:
   ```
   ns1.digitalocean.com → Cloudflare nameservers
   ns2.digitalocean.com
   ```

2. **In Cloudflare Dashboard:**
   - Zone: `nextslot.in`
   - Create A record:
     ```
     Name: @
     Type: A
     Value: your-digitalocean-app-ip
     Proxied: Yes
     ```

3. **Set Fallback Origin:**
   ```
   API Endpoint: /zones/{zone_id}/custom_hostnames/fallback_origin
   
   Payload:
   {
     "origin": "your-app.ondigitalocean.app"
   }
   ```

4. **Test with script:**
   ```bash
   python fix_cloudflare.py
   python test_cloudflare.py
   ```

---

## Step 4: Configure Django Settings for DigitalOcean

### Update `booking_saas/settings.py`

```python
# ============================================================================
# DIGITALOCEAN CONFIGURATION
# ============================================================================

# Your DigitalOcean App Platform domain or Droplet IP
DIGITALOCEAN_APP_DOMAIN = config('DIGITALOCEAN_APP_DOMAIN', 
    default='nextslot-xyz.ondigitalocean.app')

# Update ALLOWED_HOSTS for DigitalOcean
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'nextslot.in',
    'www.nextslot.in',
    'customers.nextslot.in',
    DIGITALOCEAN_APP_DOMAIN,
    '.nextslot.in',  # All subdomains
    '*'  # Accept all (validated in middleware)
]

# Railway/Droplet app domain (for Cloudflare fallback)
RAILWAY_DOMAIN = config('RAILWAY_DOMAIN', 
    default=DIGITALOCEAN_APP_DOMAIN)

# Cloudflare configuration (same as before)
CLOUDFLARE_API_TOKEN = config('CLOUDFLARE_API_TOKEN', default='')
CLOUDFLARE_ZONE_ID = config('CLOUDFLARE_ZONE_ID', default='')
CLOUDFLARE_CNAME_TARGET = config('CLOUDFLARE_CNAME_TARGET', 
    default=f'customers.{DEFAULT_DOMAIN}')

# Security for production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
```

### Update `.env` for DigitalOcean

```dotenv
# DigitalOcean App Configuration
DIGITALOCEAN_APP_DOMAIN=nextslot-xyz.ondigitalocean.app

# Or if using Droplet with domain:
DIGITALOCEAN_APP_DOMAIN=nextslot.in

# Production security
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# (Keep existing database, Cloudflare, etc. settings)
```

---

## Step 5: Configure Custom Domains for Providers

### For Each Provider (via Django Shell)

```bash
python manage.py shell
```

```python
from providers.models import ServiceProvider

# Get or create provider
provider = ServiceProvider.objects.get(business_name='Anju Mishra')

# Option 1: Add subdomain (instant, no DNS needed)
provider.custom_domain = 'anju.nextslot.in'
provider.custom_domain_type = 'subdomain'
provider.domain_verified = True
provider.ssl_enabled = True
provider.save()
print(f"✓ Subdomain created: {provider.custom_domain}")

# Option 2: Add custom domain (requires DNS)
provider.custom_domain = 'anjalbeauty.com'
provider.custom_domain_type = 'domain'
provider.domain_verified = False  # Will verify after DNS setup
provider.cloudflare_hostname_id = ''  # Will be set by Cloudflare API
provider.save()
print(f"✓ Custom domain added: {provider.custom_domain}")
```

### Using Admin Interface

1. Go to Django Admin: `https://yourdomain.com/admin/`
2. Find ServiceProvider
3. Edit provider:
   - `custom_domain`: `anju.nextslot.in` or `yourdomain.com`
   - `custom_domain_type`: `subdomain` or `domain`
   - `domain_verified`: Check when DNS is ready
   - `ssl_enabled`: Check when SSL is active

### Via Provider Dashboard (User Self-Service)

Provider logs in and goes to: **Dashboard → Custom Domain**
- Choose subdomain or custom domain
- For subdomains: instant activation
- For custom domains: follow DNS setup instructions

---

## Step 6: DNS Setup for Custom Domains

### For Provider's Own Domain

Provider needs to add CNAME record at their registrar:

**Example: Provider using GoDaddy**

1. Go to: GoDaddy → Manage DNS
2. Add CNAME record:
   ```
   Name: @ (or subdomain like "book")
   Type: CNAME
   Value: customers.nextslot.in
   TTL: 3600
   ```
3. Wait 24-48 hours for propagation
4. Verify: `nslookup yourdomain.com`

**Example: Provider using Namecheap**

1. Go to: Namecheap → Dashboard → Manage Domain
2. Go to: Advanced DNS
3. Add CNAME:
   ```
   Host: @ or book
   Type: CNAME Record
   Value: customers.nextslot.in
   TTL: 3600
   ```

---

## Step 7: Verify Everything is Working

### Test Middleware Routing

```bash
python test_okmentor_routing.py
```

### Test Cloudflare Connection

```bash
python test_cloudflare.py
```

### Test DNS Resolution

```bash
nslookup okmentor.in
# Should show: customers.nextslot.in

nslookup salon.nextslot.in
# Should show: your-app-ip or digitalocean-app-domain
```

### Test Access

```bash
# Test subdomain
curl -H "Host: anju.nextslot.in" https://your-app-domain.ondigitalocean.app/

# Test custom domain (once DNS is ready)
curl https://okmentor.in/

# Should redirect to booking page
```

---

## Step 8: Production Checklist

- [ ] App deployed to DigitalOcean
- [ ] PostgreSQL connected and migrations applied
- [ ] Domain pointing to DigitalOcean nameservers
- [ ] Cloudflare configured with fallback origin
- [ ] Django settings updated for DigitalOcean
- [ ] SSL certificates active (automatic with Cloudflare)
- [ ] `DEBUG=False` in production
- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] Test subdomain works: `anju.nextslot.in`
- [ ] Test custom domain works: `okmentor.in` (after DNS setup)
- [ ] Middleware routing verified
- [ ] Admin accessible at `/admin/`

---

## Troubleshooting on DigitalOcean

### App won't start
```bash
# Check logs
doctl apps logs app-id --follow

# Or via DigitalOcean dashboard: Apps → Your App → Runtime Logs
```

### Database connection failed
```bash
# Verify credentials in .env
# Check DigitalOcean firewall allows connection from app
# Ensure sslmode=require in DATABASE_URL
```

### Custom domain shows 404
```bash
# Run diagnostics
python diagnose_okmentor.py

# Check DNS
nslookup yourdomain.com

# Verify Cloudflare
python test_cloudflare.py
```

### SSL certificate not active
```bash
# Check Cloudflare custom hostname status
python fix_okmentor.py

# Wait 24-48 hours for SSL issuance
```

---

## Useful Commands for DigitalOcean

### Using DigitalOcean CLI (doctl)

```bash
# Login
doctl auth init

# List apps
doctl apps list

# View app details
doctl apps get app-id

# View logs
doctl apps logs app-id --follow

# Redeploy
doctl apps create-deployment app-id

# View domains
doctl compute domain list
```

### Using SSH (if on Droplet)

```bash
# SSH into Droplet
ssh root@your-droplet-ip

# Run Django commands
cd nextslotinrailway1
python manage.py shell
python manage.py migrate
python manage.py createsuperuser
```

---

## Next Steps

1. **Deploy App** to DigitalOcean (App Platform or Droplet)
2. **Configure DNS** for your main domain
3. **Test Main Domain** works
4. **Add First Provider** with subdomain
5. **Test Subdomain** works
6. **Add Custom Domain** provider
7. **Setup DNS** at provider's registrar
8. **Monitor** Cloudflare and domain status

---

## Support Resources

- **DigitalOcean Docs**: https://docs.digitalocean.com
- **App Platform Docs**: https://docs.digitalocean.com/products/app-platform
- **PostgreSQL Docs**: https://docs.digitalocean.com/products/databases/postgresql
- **Cloudflare Docs**: https://developers.cloudflare.com

---

## Quick Reference

| Component | Configuration | Status |
|-----------|---------------|--------|
| Database | DigitalOcean PostgreSQL | ✅ Configured |
| App Host | DigitalOcean App Platform | ⏳ Deploy |
| Main Domain | nextslot.in | ⏳ Setup DNS |
| Cloudflare | For SaaS enabled | ✅ Configured |
| Custom Domains | Middleware routing | ✅ Ready |
| SSL Certificates | Automatic | ✅ Ready |

