# DNS Configuration for Each Service Provider's Custom Domain

## Overview

Each service provider needs to configure DNS records at their domain registrar to enable their custom domain to work with our Cloudflare for SaaS setup.

---

## How It Works

```
Provider's Domain (okmentor.in)
        ↓
Provider's Registrar DNS
        ↓ (CNAME points to)
Cloudflare (customers.nextslot.in)
        ↓
Django App (Middleware detects provider)
        ↓
Provider's Booking Page
```

---

## DNS Records Required

### For Each Custom Domain (e.g., okmentor.in)

**Record 1: CNAME (Main Routing)**
```
Name: @  (root domain)
Type: CNAME
Value: customers.nextslot.in
TTL: 3600
Proxied: Yes (Orange cloud)
```

**Record 2: www Subdomain (Optional)**
```
Name: www
Type: CNAME
Value: customers.nextslot.in
TTL: 3600
Proxied: Yes (Orange cloud)
```

**Record 3: TXT Records (SSL Validation)**
- Required by Cloudflare for SSL certificate issuance
- Automatically generated in Cloudflare Custom Hostnames
- Must be added at domain registrar

---

## Step-by-Step Setup for Each Provider

### For okmentor.in (Anju Mishra)

**Step 1: Provider logs into their registrar**
- Go to: GoDaddy / Namecheap / Bluehost / Hostinger (wherever okmentor.in is registered)
- Find: DNS Management or Domain Settings

**Step 2: Add CNAME Record**

**If using GoDaddy:**
```
1. Go to: My Products → okmentor.in → Manage
2. Click: DNS
3. Add Record → CNAME
4. Name: @ (or leave blank for root)
5. Value: customers.nextslot.in
6. TTL: 3600
7. Save
```

**If using Namecheap:**
```
1. Go to: My Products → okmentor.in → Manage
2. Click: Advanced DNS
3. Add New Record:
   - Host: @ (or www for www.okmentor.in)
   - Type: CNAME Record
   - Value: customers.nextslot.in
   - TTL: 3600
4. Save
```

**If using Bluehost:**
```
1. Go to: My Hosting → okmentor.in
2. Click: Manage Domain
3. Find: DNS Zone Editor
4. Add Record:
   - Name: okmentor (or @ for root)
   - Type: CNAME
   - Points To: customers.nextslot.in
   - TTL: 3600
5. Save
```

**If using Hostinger:**
```
1. Go to: Domains → okmentor.in
2. Click: Manage → DNS Records
3. Add DNS Record:
   - Type: CNAME
   - Name: @ or okmentor
   - Content: customers.nextslot.in
   - TTL: 3600
4. Save
```

**Step 3: Check for SSL Validation Records**

Cloudflare may require additional TXT records for SSL validation:

1. Go to Cloudflare Dashboard
2. Zone: nextslot.in
3. SSL/TLS → Custom Hostnames
4. Find: okmentor.in
5. Check: Validation records (if any)
6. Add those TXT records to registrar as well

**Step 4: Wait for DNS Propagation**
- Takes: 24-48 hours
- Check: `nslookup okmentor.in`
- Should show: `customers.nextslot.in`

**Step 5: Verify in Our System**
- Email support or go to admin
- System will verify DNS is set up
- Domain becomes live

---

## Example: Complete DNS Configuration for okmentor.in

### At Registrar (GoDaddy Example)

| Name | Type | Value | TTL | Proxied |
|------|------|-------|-----|---------|
| @ | CNAME | customers.nextslot.in | 3600 | Yes |
| www | CNAME | customers.nextslot.in | 3600 | Yes |
| _acme-challenge | TXT | (Cloudflare SSL validation) | 3600 | No |

### Cloudflare Configuration

**Zone:** nextslot.in

**Custom Hostname:** okmentor.in
- Status: Active
- SSL: Active (auto-provisioned)
- CNAME Target: customers.nextslot.in

---

## Verification Steps

### Step 1: Check DNS Resolution

```bash
# Windows
nslookup okmentor.in

# Mac/Linux
dig okmentor.in

# Expected output:
# okmentor.in     3600    IN  CNAME   customers.nextslot.in
```

### Step 2: Check Cloudflare Status

```bash
# Via Cloudflare API
curl -X GET \
  "https://api.cloudflare.com/client/v4/zones/{zone_id}/custom_hostnames?hostname=okmentor.in" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "success": true,
#   "result": [{
#     "hostname": "okmentor.in",
#     "status": "active",
#     "ssl": {
#       "status": "active"
#     }
#   }]
# }
```

### Step 3: Check Access

```bash
# Should redirect to booking page
curl -L https://okmentor.in/

# Should show provider's booking page with URL: https://okmentor.in/
```

---

## Common Issues & Solutions

### Issue 1: "Domain Not Found" or 404 Error

**Cause:** DNS not yet propagated or CNAME pointing to wrong target

**Solution:**
1. Wait 24-48 hours
2. Check DNS: `nslookup okmentor.in`
3. Verify value is: `customers.nextslot.in`
4. Check registrar settings again
5. Cloudflare cache: Clear cache in Cloudflare dashboard

### Issue 2: SSL Certificate Not Active

**Cause:** SSL validation TXT records not added to registrar

**Solution:**
1. Go to Cloudflare dashboard
2. Zone: nextslot.in
3. SSL/TLS → Custom Hostnames → okmentor.in
4. Check for validation TXT records
5. Add those TXT records to registrar
6. Wait 24 hours for SSL issuance

### Issue 3: www.okmentor.in Doesn't Work

**Cause:** www subdomain CNAME not added

**Solution:**
Add second CNAME record:
```
Name: www
Type: CNAME
Value: customers.nextslot.in
TTL: 3600
```

### Issue 4: Registrar Doesn't Allow CNAME at Root

**Cause:** Some registrars don't allow CNAME at @

**Solution:**
1. Use ALIAS record if available (some registrars support it)
2. Or use A record pointing to Cloudflare's IP
3. Or contact registrar support

---

## For Multiple Custom Domains

If a provider has multiple subdomains:

```
okmentor.in → CNAME → customers.nextslot.in
book.okmentor.in → CNAME → customers.nextslot.in
www.okmentor.in → CNAME → customers.nextslot.in
```

All point to the same CNAME target. Django middleware routes based on hostname.

---

## Testing DNS Setup Locally (Before Going Live)

Add to your hosts file to test locally:

**Windows:** `C:\Windows\System32\drivers\etc\hosts`
```
127.0.0.1  okmentor.in
127.0.0.1  www.okmentor.in
```

**Mac/Linux:** `/etc/hosts`
```
127.0.0.1  okmentor.in
127.0.0.1  www.okmentor.in
```

Then test locally:
```bash
curl -H "Host: okmentor.in" http://localhost:8000/
```

---

## Checklist for Each Provider

- [ ] Domain registrar account access
- [ ] Found DNS settings
- [ ] Added CNAME record (@)
- [ ] Added CNAME record (www)
- [ ] Checked for SSL validation TXT records
- [ ] Added TXT records if required
- [ ] Saved DNS changes
- [ ] Waited 24-48 hours
- [ ] Verified DNS: `nslookup okmentor.in`
- [ ] Verified Cloudflare status
- [ ] Tested access to domain
- [ ] Provider's booking page works

---

## Troubleshooting Commands

```bash
# Check CNAME record
nslookup okmentor.in

# Check DNS propagation globally
# Use online tools:
# - https://mxtoolbox.com/mxlookup.aspx
# - https://dnschecker.org/

# Check Cloudflare custom hostname
python test_cloudflare.py

# Run diagnostics
python diagnose_okmentor.py

# Run setup script
python setup_provider_dns.py
```

---

## Next Steps

1. **For Anju Mishra (okmentor.in):**
   - Add CNAME to okmentor.in registrar
   - Wait 24-48 hours
   - Verify DNS propagates
   - Domain goes live!

2. **For Future Providers:**
   - Repeat same process for each custom domain
   - Each provider configures their own registrar
   - System routes automatically via middleware

---

## Support Resources

- **Cloudflare Docs:** https://developers.cloudflare.com/ssl/edge-certificates/custom-hostname
- **GoDaddy DNS:** https://www.godaddy.com/help/manage-dns-records-680
- **Namecheap DNS:** https://www.namecheap.com/support/knowledgebase/article.aspx/319/2176/how-do-i-set-up-a-cname-record
- **Bluehost DNS:** https://www.bluehost.com/help/article/how-to-add-dns-records
- **Hostinger DNS:** https://www.hostinger.com/help/article/how-to-manage-dns-records

