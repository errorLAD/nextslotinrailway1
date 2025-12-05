# Simple DNS + SSL Setup Guide

## Overview

Custom domains now use simple DNS records instead of Cloudflare Custom Hostnames API.

**What providers need to do:**
1. Add a simple CNAME record to their DNS
2. Wait for DNS propagation
3. SSL certificate is automatic (Let's Encrypt)

**What you need to do:**
1. Setup wildcard SSL for *.nextslot.in
2. Configure your app to serve multiple domains
3. Monitor DNS propagation

---

## How It Works

### Provider's Setup (Provider does this)

**Providers receive:**
```
Domain: okmentor.in
CNAME Record:
  - Record Type: CNAME
  - Record Name: @ (or www)
  - Record Value: app.nextslot.in
  - TTL: 3600
```

**Provider adds this to their DNS provider** (GoDaddy, Namecheap, Route53, etc.)

**DNS Propagation Timeline:**
- 5-10 minutes: Usually active
- 10-30 minutes: Most cases
- 30-48 hours: May take this long to propagate globally

### Traffic Flow

```
User visits: okmentor.in
    ↓
Browser resolves DNS
    ↓
Finds CNAME: okmentor.in → app.nextslot.in
    ↓
Connects to: app.nextslot.in
    ↓
Your app receives request
    ↓
Django middleware routes to provider's pages
    ↓
Provider's booking page loads
    ↓
✅ Works!
```

---

## Admin Setup (What You Do)

### 1. Set App Domain in Settings

```python
# settings.py
DIGITALOCEAN_APP_DOMAIN = 'app.nextslot.in'  # Your app domain
APP_IP_ADDRESS = '123.45.67.89'  # Optional fallback IP
```

### 2. Setup Wildcard SSL Certificate

For all provider subdomains (*.nextslot.in):

```bash
# Using certbot
sudo certbot certonly --dns-cloudflare \
  -d '*.nextslot.in' \
  -d 'nextslot.in' \
  --dns-cloudflare-credentials ~/.cloudflare.ini
```

**Or using Docker:**

```bash
docker run -it --rm \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly \
  --dns-cloudflare \
  -d '*.nextslot.in' \
  -d 'nextslot.in'
```

### 3. Configure Django for Multiple Domains

```python
# settings.py

ALLOWED_HOSTS = [
    'nextslot.in',
    '*.nextslot.in',
    'app.nextslot.in',
    '*'  # For custom provider domains
]
```

### 4. Setup Middleware for Domain Routing

Your middleware already handles this, but verify:

```python
# providers/middleware.py - already exists
# Routes based on domain to show correct provider

def domain_middleware(get_response):
    def middleware(request):
        # Extract domain from Host header
        host = request.get_host()
        # Route to correct provider
        return get_response(request)
    return middleware
```

---

## SSL Certificate Options

### Option 1: Wildcard Certificate (Recommended)
- Covers: *.nextslot.in and nextslot.in
- Cost: FREE (Let's Encrypt)
- Renewal: Automatic (every 90 days)
- Setup time: 15 minutes

```bash
certbot certonly --dns-cloudflare -d '*.nextslot.in' -d 'nextslot.in'
```

**Certificate will be located at:**
- `/etc/letsencrypt/live/nextslot.in/fullchain.pem`
- `/etc/letsencrypt/live/nextslot.in/privkey.pem`

### Option 2: Individual Certificates Per Provider
- Setup: More complex
- Cost: FREE per domain (Let's Encrypt)
- Not recommended (too many certs to manage)

### Option 3: Commercial Multi-SAN Certificate
- Setup: Manual
- Cost: $50-200/year
- Covers: 50-500 custom provider domains
- Recommended for: Enterprise customers

---

## For Provider Custom Domains (okmentor.in)

Providers with their own registrars can also add SSL:

**Option A: Let's Encrypt on Their Domain**
```bash
# Provider runs this
certbot certonly --dns-01 -d okmentor.in

# Then points to your app with CNAME
okmentor.in CNAME app.nextslot.in
```

**Option B: You Provide SSL**
```
Provider adds CNAME:
  okmentor.in → app.nextslot.in

Your app serves SSL for okmentor.in:
  - Certificate: okmentor.in (individual cert)
  - Or: Multi-SAN cert covering all domains
```

**Option C: Self-Signed (Not Recommended)**
- Only for testing
- Browsers show warning
- Not suitable for production

---

## DNS Setup Instructions (Send to Providers)

```
=== CUSTOM DOMAIN SETUP ===

Your Domain: okmentor.in
Our App Domain: app.nextslot.in

STEP 1: Add DNS Record
  Go to your domain registrar (GoDaddy, Namecheap, etc.)
  Add this record:
  
  Type: CNAME
  Name: @ (or www)
  Value: app.nextslot.in
  TTL: 3600
  
  Click Save

STEP 2: Wait for DNS
  DNS propagation: 5 minutes to 48 hours
  Check status: https://www.mxtoolbox.com/mxlookup/
  
  Enter: okmentor.in
  Should show: okmentor.in CNAME app.nextslot.in

STEP 3: SSL Certificate
  Once DNS is verified, SSL is automatic!
  Takes 5-15 minutes after DNS is live
  
  You'll see green lock 🔒 in browser

STEP 4: Done!
  Your domain now works:
  https://okmentor.in
  
  No other action needed!

Questions? Contact: support@nextslot.in
```

---

## Checking DNS Status

### For Providers (Check themselves)

**Online checker:**
https://www.mxtoolbox.com/mxlookup/
- Enter domain: okmentor.in
- Should show CNAME record

**Command line:**
```bash
# Linux/Mac
dig okmentor.in CNAME
nslookup okmentor.in

# Windows
nslookup okmentor.in
```

### Admin Check (You check)

```bash
# Check DNS record
dig okmentor.in CNAME

# Check SSL certificate
openssl s_client -connect app.nextslot.in:443

# Check website loads
curl -I https://okmentor.in
# Should return HTTP 200, not 404
```

---

## Troubleshooting

### Issue: DNS shows "Pending" or "Not Configured"

**Causes:**
- Provider hasn't added CNAME yet
- DNS hasn't propagated
- Wrong CNAME value entered

**Solution:**
1. Ask provider to verify CNAME in their DNS panel
2. Check: `dig okmentor.in CNAME`
3. Should show: `okmentor.in CNAME app.nextslot.in`
4. Wait 5-48 hours for full propagation

### Issue: Domain Shows "Cannot Connect"

**Causes:**
- DNS not configured yet
- Your app not running
- Firewall blocking

**Solution:**
1. Check DNS: `dig okmentor.in`
2. Check app: `curl -I https://app.nextslot.in`
3. Check firewall: Ensure port 443 open
4. Wait for DNS propagation

### Issue: SSL Certificate Not Valid

**Causes:**
- Certificate not installed yet
- Wrong domain in certificate
- Certificate expired

**Solution:**
1. Check cert: `openssl s_client -connect app.nextslot.in:443`
2. Verify domain in cert matches
3. Check expiration: Should be ~90 days
4. Renew if needed: `certbot renew`

### Issue: Domain Works But SSL Shows Error

**Causes:**
- Visiting HTTP instead of HTTPS
- Certificate for different domain
- Intermediate cert missing

**Solution:**
1. Use HTTPS: https://okmentor.in
2. Check certificate domain
3. Update Django SSL settings:
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
```

---

## SSL Certificate Renewal

### Automatic Renewal (Recommended)

```bash
# Setup auto-renewal
sudo systemctl enable certbot-renew.timer
sudo systemctl start certbot-renew.timer

# Check renewal timer
sudo systemctl status certbot-renew.timer
```

### Manual Renewal

```bash
# Renew all certificates
sudo certbot renew

# Renew specific certificate
sudo certbot renew --cert-name nextslot.in
```

### Renewal Timeline

- Certificate valid for: 90 days
- Renewal attempted at: Day 60
- If renewal fails, tries daily after day 60
- Before renewal completes, domain stops working

**Always test renewal:**
```bash
sudo certbot renew --dry-run
```

---

## Performance & Limits

### DNS
- Max domains: Unlimited
- Propagation: 5 minutes to 48 hours
- Cost: FREE

### SSL Certificates
- Free via Let's Encrypt: 50/week new domains
- Renewal: Unlimited
- Cost: FREE

### Your App
- Max concurrent: Based on resources
- Load balancing: Add more servers
- CDN: Optional (Cloudflare, etc.)

---

## Monitoring & Alerts

### Setup Monitoring

```bash
# Monitor DNS for provider domains
0 */6 * * * /usr/local/bin/check-provider-dns.sh

# Check SSL expiration
0 0 * * * /usr/local/bin/check-ssl-expiry.sh

# Monitor app health
*/5 * * * * /usr/local/bin/health-check.sh
```

### Alert System

Monitor these:
1. DNS changes for registered domains
2. SSL certificate expiration (alert at 30 days)
3. Domain accessibility (HTTP status)
4. SSL validity (check cert status)

---

## Cost Breakdown

| Component | Cost | Renewal |
|-----------|------|---------|
| DNS Records | FREE | N/A |
| Wildcard SSL | FREE (Let's Encrypt) | Auto (90 days) |
| App Domain | Included | Included |
| Custom Provider Domain | Provider pays | Provider pays |
| Admin overhead | Your time | Your time |

**Total for you: $0**

---

## Summary

✅ **Providers:**
- Add simple CNAME record
- Wait for DNS propagation
- SSL is automatic
- Domain works!

✅ **You (Admin):**
- Setup wildcard SSL (one time)
- Configure Django
- Monitor DNS/SSL
- Support providers

✅ **Benefits:**
- Simple (just DNS records)
- Free SSL
- Scalable (unlimited domains)
- No Cloudflare API needed
- Provider friendly

---

## Next Steps

1. Run: `setup_simple_ssl.sh` (when created)
2. Send DNS instructions to providers
3. Monitor first few domains
4. Setup alerts
5. Done!

Questions? Check the logs or contact support.
