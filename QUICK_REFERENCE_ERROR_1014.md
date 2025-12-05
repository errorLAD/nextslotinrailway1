# ⚡ Quick Reference Card - Error 1014 Solution

## The Problem (2 seconds)
Custom domains show: **Error 1014: CNAME Cross-User Banned**  
Reason: Cloudflare blocks manual CNAME across different accounts

## The Solution (2 seconds)
Use **Cloudflare Custom Hostnames API** instead of manual CNAME  
Result: Automatic setup, no Error 1014, SSL included

---

## 5-Step Fix (15 minutes)

### 1️⃣ Verify Config (2 min)
```bash
python verify_cloudflare_config.py
```
✅ If green → proceed to step 2  
❌ If red → follow recommendations shown

### 2️⃣ Configure Cloudflare (3 min, if needed)
- https://dash.cloudflare.com/
- Select: nextslot.in zone
- Settings → For SaaS → Enable Custom Hostnames
- Set Fallback Origin: nextslot-app.ondigitalocean.app

### 3️⃣ Create API Token (2 min, if needed)
- https://dash.cloudflare.com/
- Account → API Tokens → Create Token
- Copy it, set: CLOUDFLARE_API_TOKEN=your_token

### 4️⃣ Run Setup (5 min)
```bash
python setup_cloudflare_custom_hostnames.py
```
✅ Setup complete when you see: "🎉 All custom hostnames created successfully!"

### 5️⃣ Wait & Test (5 min + 5-30 min DNS)
- Wait 5-30 minutes for DNS propagation
- Visit a provider domain in browser
- ✅ Should see booking page (not Error 1014!)
- ✅ SSL should be active (green lock 🔒)

---

## Environment Variables (Copy & Paste)

```bash
# Get these from https://dash.cloudflare.com/
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_ZONE_ID=your_zone_id_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
DIGITALOCEAN_APP_DOMAIN=nextslot-app.ondigitalocean.app
```

---

## Common Commands

### Check Configuration
```bash
python verify_cloudflare_config.py
```

### Setup All Domains
```bash
python setup_cloudflare_custom_hostnames.py
```

### Check Specific Domain
```bash
python manage.py shell
from providers.cloudflare_saas import verify_custom_hostname
verify_custom_hostname('okmentor.in')
```

### Count Active Domains
```bash
python manage.py shell
from providers.models import ServiceProvider
count = ServiceProvider.objects.filter(custom_domain__isnull=False).exclude(custom_domain='').count()
print(f"Active: {count}")
```

---

## Troubleshooting (30 seconds)

| Problem | Fix |
|---------|-----|
| Error 1014 still showing | Wait 5-30 min, clear browser cache, check Cloudflare dashboard |
| API token invalid | Get new token, set CLOUDFLARE_API_TOKEN |
| Zone not found | Check CLOUDFLARE_ZONE_ID is 32 characters |
| Pending status | NORMAL! Cloudflare is setting up. Wait. |
| Script fails | Run verify_cloudflare_config.py to see what's missing |

---

## What to Send to Providers

📧 Send this file: **`PROVIDER_CUSTOM_DOMAIN_GUIDE.md`**

It explains:
- ✅ How to add their domain
- ✅ What happens next
- ✅ When it will be ready
- ✅ FAQ section

---

## Documentation Files

| File | Read Time | Purpose |
|------|-----------|---------|
| ERROR_1014_SOLUTION_INDEX.md | 5 min | Complete guide |
| FIX_ERROR_1014_QUICK_STEPS.md | 3 min | This document |
| ADMIN_CUSTOM_DOMAIN_SETUP.md | 15 min | Detailed setup |
| PROVIDER_CUSTOM_DOMAIN_GUIDE.md | 5 min | Send to providers |

---

## Key Facts

✅ **Free:** Cloudflare for SaaS is included (100 domains free)  
✅ **Time:** 15 min setup + 5-30 min DNS = 45 min total  
✅ **Scale:** Works for unlimited providers  
✅ **SSL:** Automatic DV certificates  
✅ **Easy:** Fully automatic (no manual DNS)  

---

## Success Checklist

- [ ] Ran verify_cloudflare_config.py ✅
- [ ] All settings configured
- [ ] Ran setup_cloudflare_custom_hostnames.py
- [ ] Waited 5-30 minutes
- [ ] Tested domain in browser
- [ ] ✅ No Error 1014!
- [ ] ✅ SSL is active!
- [ ] ✅ Done!

---

## Emergency Revert

If everything breaks:
```bash
git log --oneline -5
git revert <commit_hash>
```

But it shouldn't! 😊

---

## Now What?

👉 **Read:** `FIX_ERROR_1014_QUICK_STEPS.md`

**Time to fix:** 15 minutes ⏱️

---

**Status: ✅ READY FOR DEPLOYMENT**

All documentation, scripts, and code are ready.  
Just follow the 5 steps above!

🚀 Let's fix those custom domains!
