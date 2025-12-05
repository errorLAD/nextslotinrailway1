# Quick Fix for Cloudflare Error 1014 - Action Steps

## TL;DR - What You Need To Do

The issue: Cloudflare Error 1014 when providers try to use their custom domains.

**The fix has 3 simple steps:**

### Step 1: Enable Cloudflare for SaaS (5 minutes)
1. Go to: https://dash.cloudflare.com/
2. Select your zone: `nextslot.in`
3. Go to: Settings → For SaaS
4. Click: "Enable Custom Hostnames"
5. Set Fallback origin: `nextslot-app.ondigitalocean.app`
6. Click: Save

### Step 2: Create API Token (5 minutes)
1. Go to: https://dash.cloudflare.com/
2. Left sidebar: Account → API Tokens
3. Click: "Create Token"
4. Use template: "Custom Hostname Setup" or create custom with:
   - Permissions: Zone.Custom Hostnames (Edit, Read)
   - Zone: Select `nextslot.in`
5. Copy the token

### Step 3: Configure Environment Variables (2 minutes)

Set these in your deployment environment:
```bash
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_ZONE_ID=your_zone_id_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

**To get Zone ID and Account ID:**
- Go to: https://dash.cloudflare.com/
- Select zone: `nextslot.in`
- Right sidebar shows: Zone ID (copy it)
- Account ID is in Account dropdown at top left

### Step 4: Run Setup Script (1 minute)
```bash
python setup_cloudflare_custom_hostnames.py
```

**That's it!** Your domains will now work without Error 1014!

---

## What Changed?

### Before (Manual CNAME - Broken)
```
Provider domain → Manual CNAME record → Cross-account CNAME
                                          ❌ ERROR 1014!
```

### After (Custom Hostnames API - Fixed)
```
Provider domain + System API call → Cloudflare handles routing
                                     ✅ Works perfectly!
                                     ✅ No manual CNAME!
                                     ✅ SSL auto-provisioned!
```

---

## Why This Fix Works

**The Problem:**
- Provider has domain in THEIR Cloudflare account
- You're trying to CNAME it to nextslot.in in YOUR account
- Cloudflare blocks this for security (Error 1014)

**The Solution:**
- Use Cloudflare Custom Hostnames API
- No manual CNAME records needed
- Cloudflare handles routing internally
- No cross-account issues!

---

## Provider Experience

**What providers see:**
1. ✅ Add their domain to app
2. ✅ Wait 5-30 minutes
3. ✅ Domain automatically works!
4. ✅ SSL certificate active!

**No manual DNS configuration needed!**

---

## Troubleshooting

### Problem: "Custom Hostnames not enabled"

**Solution:**
1. Go to Cloudflare dashboard
2. Select nextslot.in zone
3. Settings → For SaaS
4. Enable "Custom Hostnames"

### Problem: "API token invalid"

**Solution:**
1. Create new API token
2. Grant permissions: Zone.Custom Hostnames (Edit, Read)
3. Set resource: nextslot.in zone
4. Copy entire token (not account ID)

### Problem: "Zone ID not found"

**Solution:**
1. Go to: https://dash.cloudflare.com/
2. Click on nextslot.in zone
3. Right sidebar shows Zone ID
4. Click to copy it

### Problem: "Still seeing Error 1014"

**Solution:**
1. Delete any manual CNAME records from provider's Cloudflare
2. Run: `python setup_cloudflare_custom_hostnames.py`
3. Wait 10 minutes for DNS propagation
4. Test again

### Problem: Domain shows "pending" status

**This is normal!** Cloudflare is:
- Processing the custom hostname
- Issuing SSL certificate
- Setting up routing

**Just wait 5-30 minutes.** Status will become "active" automatically.

---

## Files Changed

1. **setup_cloudflare_custom_hostnames.py** - New setup script
2. **FIX_ERROR_1014_CNAME_CROSS_USER.md** - Detailed explanation
3. **providers/domain_views.py** - Updated messages (no manual CNAME!)
4. **providers/cloudflare_saas.py** - Already has Custom Hostnames API

## Testing

To test if the fix works:

1. **Setup:**
   ```bash
   python setup_cloudflare_custom_hostnames.py
   ```

2. **Check status:**
   ```bash
   python manage.py shell
   >>> from providers.cloudflare_saas import get_custom_hostname
   >>> get_custom_hostname('www.okmentor.in')
   ```

3. **Visit domain:**
   - Open: https://www.okmentor.in
   - Should see booking page (not Error 1014!)

---

## Next Steps

1. ✅ Enable Cloudflare for SaaS
2. ✅ Create API token
3. ✅ Set environment variables
4. ✅ Run setup script
5. ✅ Wait for DNS propagation (5-30 mins)
6. ✅ Test provider domains

**Questions?** Check FIX_ERROR_1014_CNAME_CROSS_USER.md for detailed technical info.
