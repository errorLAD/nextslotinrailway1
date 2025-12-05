# Multi-Domain Quick Reference

## 🎯 TL;DR - Your Website Already Supports Multi-Domain!

Each service provider can have their own domain:
- **Instant**: `salon.nextslot.in` (subdomain)
- **Branded**: `yourdomain.com` (custom domain)

✅ **Status**: Fully configured and ready to use

---

## ⚡ Quick Commands

### Check System Status
```bash
python verify_multi_domain.py
```

### Fix Cloudflare Setup
```bash
python fix_cloudflare.py
```

### Test Cloudflare Connection
```bash
python test_cloudflare.py
```

---

## 🔧 Add Domain to a Provider

### Option 1: In Django Shell
```bash
python manage.py shell

from providers.models import ServiceProvider

provider = ServiceProvider.objects.get(business_name='Provider Name')

# Add subdomain (instant - no DNS needed)
provider.custom_domain = 'customname.nextslot.in'
provider.custom_domain_type = 'subdomain'
provider.domain_verified = True
provider.ssl_enabled = True
provider.save()

# OR add custom domain (requires DNS + 24-48 hours)
provider.custom_domain = 'yourdomain.com'
provider.custom_domain_type = 'domain'
provider.domain_verified = False
provider.save()
```

### Option 2: In Admin Interface
1. Go to Django Admin
2. Find ServiceProvider
3. Edit the fields:
   - `custom_domain`
   - `custom_domain_type`
   - `domain_verified` (check when DNS is ready)

### Option 3: Provider Self-Service
1. Provider logs in
2. Go to Dashboard → Custom Domain
3. Choose subdomain or custom domain
4. For custom domain: follow DNS setup instructions
5. Done!

---

## 📋 DNS Setup for Custom Domains

### What Provider Needs to Do

1. **Go to their domain registrar** (GoDaddy, Namecheap, etc.)
2. **Add DNS record**:
   ```
   Name: @ (or your desired subdomain)
   Type: CNAME
   Value: customers.nextslot.in
   ```
3. **Wait 24-48 hours** for propagation
4. **Verify in app**

### Verify DNS in Terminal
```bash
nslookup yourdomain.com
# Should show: customers.nextslot.in

# Or for subdomains:
nslookup salon.nextslot.in
# Should show: web-production-200fb.up.railway.app
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Domain in list but doesn't work | Check DNS CNAME record exists and wait 24-48 hours |
| SSL not showing as active | Verify Cloudflare status: `python test_cloudflare.py` |
| Provider can't add domain | Check provider is on PRO plan |
| Subdomain not working | Verify subdomain is formatted correctly (no www) |
| Multiple providers same domain | This shouldn't happen - database validates uniqueness |

### Quick Fix Command
```bash
# Manually mark domain as verified (after DNS is ready)
python manage.py shell

provider = ServiceProvider.objects.get(custom_domain='yourdomain.com')
provider.domain_verified = True
provider.ssl_enabled = True
provider.save()

print("Domain verified!")
```

---

## 📊 Key Files

| File | What It Does |
|------|-------------|
| `providers/middleware.py` | Routes domain to provider |
| `providers/domain_views.py` | Domain management UI |
| `providers/cloudflare_saas.py` | Cloudflare API calls |
| `test_cloudflare.py` | Check Cloudflare status |
| `fix_cloudflare.py` | Configure Cloudflare |
| `verify_multi_domain.py` | Verify all domains |

---

## 🧪 Test It Yourself

### Test 1: Add Subdomain
```bash
python manage.py shell

from providers.models import ServiceProvider
p = ServiceProvider.objects.first()
p.custom_domain = 'test.nextslot.in'
p.custom_domain_type = 'subdomain'
p.domain_verified = True
p.save()

# Now try accessing in browser (requires DNS or hosts entry)
```

### Test 2: Check Middleware Works
```bash
curl -H "Host: test.nextslot.in" http://localhost:8000/
# Should redirect to provider's booking page
```

### Test 3: Verify Database
```bash
python manage.py shell

from providers.models import ServiceProvider

# Find provider with custom domain
p = ServiceProvider.objects.get(custom_domain__isnull=False).exclude(custom_domain='').first()

if p:
    print(f"Provider: {p.business_name}")
    print(f"Domain: {p.custom_domain}")
    print(f"Verified: {p.domain_verified}")
    print(f"SSL: {p.ssl_enabled}")
```

---

## 📱 What Provider Sees

### Subdomain (Instant)
```
Step 1: Provider enters "mysalon" in dashboard
Step 2: System creates: mysalon.nextslot.in
Step 3: INSTANT ✓ - Domain is live immediately
Step 4: No DNS changes needed
Step 5: Provider can share: https://mysalon.nextslot.in
```

### Custom Domain (24-48 hours)
```
Step 1: Provider enters "mysalon.com" in dashboard
Step 2: System shows instructions:
        "Add CNAME record: mysalon.com → customers.nextslot.in"
Step 3: Provider goes to their registrar
Step 4: Adds the DNS record
Step 5: Waits 24-48 hours
Step 6: Verifies in app
Step 7: Provider can share: https://mysalon.com
```

---

## 🎓 How It Works Under the Hood

```
User visits: okmentor.in
       ↓
Cloudflare catches it
       ↓
Routes to: customers.nextslot.in (Railway app)
       ↓
Django receives request with Host: okmentor.in
       ↓
CustomDomainMiddleware checks:
  "Is okmentor.in in database? YES → Anju Mishra"
       ↓
Redirects to: /appointments/book/anju-mishra/
       ↓
User sees: https://okmentor.in (URL unchanged)
         Content: Anju Mishra's booking page
```

---

## 💰 Pricing

| Feature | FREE Plan | PRO Plan |
|---------|-----------|---------|
| Custom Domain | ❌ | ✅ |
| Subdomains | ❌ | ✅ |
| SSL Certificate | ❌ | ✅ (auto) |
| Cloudflare Setup | ❌ | ✅ |

---

## 🚀 Next Steps

1. **Test with existing provider**:
   - okmentor.in is already configured
   - Add CNAME to DNS registrar
   - Verify status

2. **Add new provider**:
   - Upgrade to PRO plan
   - Go to Dashboard → Custom Domain
   - Choose subdomain or custom domain

3. **Monitor**:
   - Run `python test_cloudflare.py` weekly
   - Check provider domains are accessible

---

## ❓ Questions?

See detailed docs:
- `MULTI_DOMAIN_SETUP.md` - Complete setup
- `MULTI_DOMAIN_CONFIG_COMPLETE.md` - Full configuration
- `MULTI_DOMAIN_ARCHITECTURE.md` - Technical architecture

