# Admin Guide: Fix and Monitor Custom Domains

## Problem Summary

**Error 1014: CNAME Cross-User Banned**

When providers use custom domains (e.g., `www.okmentor.in`), Cloudflare blocks the request with Error 1014.

**Root Cause:** 
- Trying to CNAME across different Cloudflare accounts
- Provider's domain in their account, our system in our account
- Cloudflare security blocks this

**Solution:**
- Use Cloudflare Custom Hostnames API instead of manual CNAME
- Cloudflare handles routing internally (no cross-account issues)
- Automatic SSL provisioning
- Zero manual DNS configuration

---

## Quick Setup (Admin Only)

### 1. Verify Configuration (5 minutes)

```bash
python verify_cloudflare_config.py
```

This checks:
- ✅ CLOUDFLARE_API_TOKEN is set
- ✅ CLOUDFLARE_ZONE_ID is set
- ✅ Connection to Cloudflare works
- ✅ Custom Hostnames feature is available
- ✅ API token has correct permissions

### 2. If Configuration Missing

**Set these environment variables:**

```bash
CLOUDFLARE_API_TOKEN=your_api_token
CLOUDFLARE_ZONE_ID=your_zone_id
CLOUDFLARE_ACCOUNT_ID=your_account_id
DIGITALOCEAN_APP_DOMAIN=nextslot-app.ondigitalocean.app
```

**To get these values:**

1. **API Token:**
   - Go: https://dash.cloudflare.com/
   - Account → API Tokens → Create Token
   - Template: "Custom Hostname Setup" (recommended)
   - Or custom: Zone.Custom Hostnames (Edit, Read)
   - Copy the token

2. **Zone ID:**
   - Go: https://dash.cloudflare.com/
   - Select nextslot.in zone
   - Right sidebar shows Zone ID
   - Copy it

3. **Account ID:**
   - Go: https://dash.cloudflare.com/
   - Account dropdown (top-left)
   - Copy Account ID

4. **DigitalOcean Domain:**
   - Go: https://cloud.digitalocean.com/
   - Apps → Your app
   - Copy the app domain

### 3. Enable Cloudflare for SaaS

**In Cloudflare Dashboard:**

1. Select zone: `nextslot.in`
2. Settings → For SaaS
3. Enable: "Custom Hostnames"
4. Set Fallback Origin: `nextslot-app.ondigitalocean.app`
5. Save

### 4. Setup All Provider Domains

```bash
python setup_cloudflare_custom_hostnames.py
```

This will:
- ✅ Check all providers with custom domains
- ✅ Create Custom Hostname for each in Cloudflare
- ✅ Trigger SSL certificate provisioning
- ✅ Show status for each

**Expected output:**
```
Setting up: okmentor.in (Provider: Ramesh Salon)
  ✅ Success!
     - Hostname ID: abcd1234...
     - Status: pending
     - Next: Cloudflare will issue SSL cert (5-30 mins)
```

### 5. Wait and Monitor

DNS propagation takes:
- ⏱️ **5-10 minutes:** Usually active
- ⏱️ **10-30 minutes:** Most cases  
- ⏱️ **30-60 minutes:** Rare cases

During this time, domain status is "pending" (normal).

### 6. Verify Domains Are Active

```bash
python manage.py shell
```

```python
from providers.cloudflare_saas import verify_custom_hostname
from providers.models import ServiceProvider

# Check a specific provider
provider = ServiceProvider.objects.get(business_name='Ramesh Salon')
status = verify_custom_hostname(provider.custom_domain)
print(status)

# Should show:
# {
#     'success': True,
#     'status': 'active',
#     'is_verified': True,
#     'ssl_active': True
# }
```

---

## Troubleshooting

### Issue: Domain shows Error 1014

**Still happening after setup?**

1. **Verify configuration:**
   ```bash
   python verify_cloudflare_config.py
   ```

2. **Check Custom Hostname status:**
   ```bash
   python manage.py shell
   from providers.cloudflare_saas import get_custom_hostname
   get_custom_hostname('okmentor.in')
   ```

3. **Check if provider has manual CNAME:**
   - Ask provider to delete any manual CNAME records
   - CNAME setup should be automatic, not manual

4. **Check Cloudflare dashboard:**
   - https://dash.cloudflare.com/
   - Select nextslot.in zone
   - Look for Custom Hostnames section
   - Should see the domain listed

### Issue: Custom Hostname in "pending" status

This is **normal**! Cloudflare is:
- Processing the request
- Issuing SSL certificate
- Setting up routing

**Typical timeline:**
- 0-2 mins: Pending (DNS created)
- 2-5 mins: SSL validation (validation records added)
- 5-30 mins: Certificate issued → Status becomes "active"

**Just wait.** Status will change automatically.

### Issue: API token invalid

1. Check token is complete (no spaces, full length)
2. Create new token if needed
3. Ensure permissions include "Zone.Custom Hostnames"
4. Set correct environment variable

### Issue: Zone ID not found

1. Verify you're looking at nextslot.in zone
2. Zone ID should be 32 characters
3. Copy from right sidebar in Cloudflare dashboard

### Issue: "Custom Hostnames feature not available"

Solution:
1. Go to Cloudflare dashboard
2. Select nextslot.in zone
3. Settings → For SaaS
4. Enable "Custom Hostnames"
5. Set Fallback Origin to your app domain

### Issue: Some providers fail to setup

Check the error message. Common issues:

```
Error: "Duplicate hostname"
→ Domain already exists in Cloudflare
→ Delete it first, then run setup again

Error: "Invalid API token"
→ API token has wrong permissions or is invalid
→ Create new token with correct permissions

Error: "Zone not found"
→ CLOUDFLARE_ZONE_ID is wrong
→ Copy correct Zone ID from Cloudflare
```

---

## Monitoring

### Check Provider Domain Status

```python
from providers.models import ServiceProvider
from providers.cloudflare_saas import verify_custom_hostname

provider = ServiceProvider.objects.get(pk=provider_id)

# Check status
status = verify_custom_hostname(provider.custom_domain)

if status['is_verified']:
    print(f"✅ {provider.custom_domain} is active!")
else:
    print(f"⏳ {provider.custom_domain} is pending")
    print(f"   Status: {status['status']}")
```

### Database Fields to Monitor

Each ServiceProvider has:
- `custom_domain`: The provider's custom domain
- `cloudflare_hostname_id`: Cloudflare's unique ID for this domain
- `txt_record_name`: For TXT record verification (if needed)
- `domain_verification_code`: Verification code
- `domain_verified`: Boolean (verified?)
- `ssl_enabled`: Boolean (SSL active?)

Check them in Django admin:
1. Go: /admin/providers/serviceprovider/
2. Select provider
3. Look for "Custom Domain Information" section

### Cloudflare Dashboard Monitoring

Monitor directly in Cloudflare:

1. Go: https://dash.cloudflare.com/
2. Select nextslot.in zone
3. Custom Hostnames section shows all active domains
4. Click any domain to see:
   - Current status
   - SSL certificate info
   - Recent changes

---

## Removing Domains

If a provider wants to remove their custom domain:

**Option 1: Provider Self-Service**
- Provider goes to dashboard
- Settings → Custom Domain → Remove
- System automatically removes from Cloudflare

**Option 2: Admin Manual**
```python
from providers.models import ServiceProvider
from providers.cloudflare_saas import delete_custom_hostname

provider = ServiceProvider.objects.get(pk=provider_id)

# Delete from Cloudflare
if provider.cloudflare_hostname_id:
    delete_custom_hostname(provider.cloudflare_hostname_id)

# Clear database
provider.custom_domain = None
provider.cloudflare_hostname_id = None
provider.domain_verified = False
provider.ssl_enabled = False
provider.save()
```

---

## Performance & Limits

**Cloudflare Custom Hostnames Limits:**

- Free tier: 100 custom hostnames
- Pro tier: 100+ custom hostnames
- Enterprise: Unlimited

**Your current usage:**
```bash
python manage.py shell
from providers.models import ServiceProvider

count = ServiceProvider.objects.filter(
    custom_domain__isnull=False
).exclude(custom_domain='').count()

print(f"Active custom domains: {count}")
```

---

## Billing

**Cloudflare for SaaS Costs:**

| Plan | Custom Hostnames | Cost |
|------|------------------|------|
| Free | 100 | Included |
| Pro | 100+ | $0.10 per hostname/month after first 100 |
| Business | Unlimited | Included |
| Enterprise | Unlimited | Custom pricing |

Most SaaS companies stay on Free tier with 100 domains included.

---

## Security

**Best Practices:**

1. ✅ **API Token Permissions**
   - Grant only "Zone.Custom Hostnames" permission
   - Not full zone access
   - Rotate tokens periodically

2. ✅ **Environment Variables**
   - Store in secure vault (not git)
   - Use different tokens for staging/production
   - Rotate on employee changes

3. ✅ **SSL Certificates**
   - Automatically provisioned by Cloudflare
   - DV (Domain Validated) certificates
   - Renewed automatically 30 days before expiry

4. ✅ **Provider Security**
   - Each provider gets their own domain
   - Cross-provider domains blocked
   - No domain hijacking possible

---

## Testing

### Test Custom Domain Setup

```bash
# 1. Verify config
python verify_cloudflare_config.py

# 2. Setup test provider domain
python manage.py shell
```

```python
from providers.models import ServiceProvider
from providers.cloudflare_saas import create_custom_hostname, verify_custom_hostname

# Create test domain
result = create_custom_hostname('test-okmentor.in', provider_id=1)
print(f"Created: {result}")

# Wait a few seconds
import time
time.sleep(5)

# Check status
status = verify_custom_hostname('test-okmentor.in')
print(f"Status: {status}")

# Should show 'pending' or 'active'
```

### Test Domain Resolution

```bash
# Test DNS (may not work immediately, DNS propagates)
nslookup okmentor.in
dig okmentor.in

# Test HTTPS (use browser or curl)
curl -I https://okmentor.in

# Should return:
# HTTP/1.1 200 OK
# strict-transport-security: max-age=31536000;
# (or similar success response)
```

---

## Emergency Procedures

### If All Domains Are Broken

1. **Check if system is down:**
   ```bash
   curl https://nextslot-app.ondigitalocean.app
   ```

2. **Check if Cloudflare zone is down:**
   - Go: https://dash.cloudflare.com/
   - Check for any incidents

3. **Check API connection:**
   ```bash
   python verify_cloudflare_config.py
   ```

4. **Revert custom domain changes:**
   ```bash
   git log --oneline -20  # See recent changes
   git revert <commit>     # Revert problematic commit
   ```

### If One Provider Domain Is Broken

1. **Verify configuration:**
   ```python
   provider = ServiceProvider.objects.get(pk=provider_id)
   print(f"Domain: {provider.custom_domain}")
   print(f"Verified: {provider.domain_verified}")
   print(f"Hostname ID: {provider.cloudflare_hostname_id}")
   ```

2. **Check Cloudflare status:**
   ```python
   from providers.cloudflare_saas import get_custom_hostname
   status = get_custom_hostname(provider.custom_domain)
   print(status)
   ```

3. **Recreate if needed:**
   ```python
   from providers.cloudflare_saas import create_custom_hostname, delete_custom_hostname
   
   # Delete old
   if provider.cloudflare_hostname_id:
       delete_custom_hostname(provider.cloudflare_hostname_id)
   
   # Recreate
   result = create_custom_hostname(provider.custom_domain, provider.pk)
   provider.cloudflare_hostname_id = result['hostname_id']
   provider.save()
   ```

---

## Support & Resources

**Documentation:**
- `FIX_ERROR_1014_QUICK_STEPS.md` - Quick fix guide
- `FIX_ERROR_1014_CNAME_CROSS_USER.md` - Detailed technical explanation
- `PROVIDER_CUSTOM_DOMAIN_GUIDE.md` - Guide to send to providers

**Scripts:**
- `verify_cloudflare_config.py` - Verify configuration
- `setup_cloudflare_custom_hostnames.py` - Setup all provider domains

**Cloudflare Resources:**
- Custom Hostnames API: https://developers.cloudflare.com/api/operations/zone-custom-hostnames-create-custom-hostname
- For SaaS Guide: https://developers.cloudflare.com/cloudflare-for-platforms/cloudflare-for-saas/
- Dashboard: https://dash.cloudflare.com/

**Support:**
- Contact: admin@nextslot.in
- Monitor: Check dashboard for alerts/issues
- Logs: Django logs, Cloudflare logs (in dashboard)

---

## Checklist for Setup

- [ ] Verified Cloudflare settings are configured
- [ ] Created API token with correct permissions
- [ ] Enabled "Custom Hostnames" in Cloudflare
- [ ] Set fallback origin in Cloudflare
- [ ] Run: `python verify_cloudflare_config.py` (all green)
- [ ] Run: `python setup_cloudflare_custom_hostnames.py`
- [ ] Tested with actual provider domain
- [ ] Confirmed domain is accessible (not Error 1014)
- [ ] Verified SSL certificate is active
- [ ] Notified providers that custom domains work

**When complete, you're done!** ✅
