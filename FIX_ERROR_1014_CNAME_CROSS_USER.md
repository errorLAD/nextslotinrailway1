# Fix Error 1014: CNAME Cross-User Banned

## Problem

When visiting a custom domain like `www.okmentor.in`, you get:
```
Error 1014: CNAME Cross-User Banned
```

This happens because:
1. The domain `okmentor.in` is managed in YOUR Cloudflare account
2. We're trying to CNAME it to a domain in a DIFFERENT Cloudflare account
3. Cloudflare blocks cross-account CNAMEs for security reasons

## Solution: Use Cloudflare Custom Hostnames (for SaaS)

Instead of manually adding CNAME records, use **Cloudflare Custom Hostnames API** which handles this automatically.

### How Cloudflare Custom Hostnames Works

1. **Provider adds domain**: `okmentor.in` in their Cloudflare account
2. **System creates Custom Hostname in Cloudflare**: Using API in YOUR nextslot.in zone
3. **Cloudflare automatically handles routing**: No manual CNAME records needed!
4. **SSL certificate issued automatically**: By Cloudflare

### DNS Flow (Correct Way)

```
Provider adds domain: okmentor.in (in THEIR Cloudflare account)
  ↓
System creates Custom Hostname in nextslot.in zone (YOUR Cloudflare account)
  ↓
Cloudflare automatically routes okmentor.in → nextslot-app.ondigitalocean.app
  ↓
DigitalOcean app receives request with Host: okmentor.in
  ↓
Middleware identifies provider and shows booking page
  ↓
✓ Domain works! No Error 1014!
```

## Setup Steps

### Step 1: Ensure Cloudflare for SaaS is Enabled

Go to your Cloudflare dashboard → Settings → For SaaS:
- Enable "Custom Hostnames"
- This allows you to add customer domains programmatically

### Step 2: Get Your Cloudflare Credentials

1. Go to: https://dash.cloudflare.com/
2. Select your account (for nextslot.in zone)
3. Get your credentials:
   - **Zone ID**: Right sidebar on main dashboard (copy it)
   - **API Token**: Account → API Tokens → Create Token
     - Permissions: Zone.Custom Hostnames (Edit, Read)
     - Zone Resources: Include (specific zone) → Select nextslot.in

### Step 3: Configure Environment Variables

Set these in your deployment:
```bash
CLOUDFLARE_API_TOKEN=<your-api-token>
CLOUDFLARE_ZONE_ID=<your-zone-id>
CLOUDFLARE_ACCOUNT_ID=<your-account-id>
```

### Step 4: Create Custom Hostnames for All Providers

Run this command to setup all existing providers:
```bash
python setup_cloudflare_custom_hostnames.py
```

### Step 5: Provider Instructions

When a provider wants to add their domain (e.g., `okmentor.in`):

**What they do (One-time setup)**:
1. Add the domain to their own Cloudflare account (or registrar)
2. Tell you: "I want to use okmentor.in for my booking page"

**What the system does (Automatic)**:
1. Creates a Custom Hostname in YOUR nextslot.in zone
2. Cloudflare automatically handles the routing
3. Issues SSL certificate
4. Domain is ready to use!

**That's it!** No manual CNAME records needed!

## Key Differences

### ❌ Wrong Way (Manual CNAME)
```
Provider domain → CNAME → nextslot.in CNAME → App domain
                    ↑
            Cross-account CNAME
            ❌ Error 1014!
```

### ✅ Right Way (Custom Hostnames API)
```
Provider domain + Custom Hostname API → Cloudflare handles routing automatically
                                          ✓ No Error 1014!
                                          ✓ Automatic SSL!
                                          ✓ Works immediately!
```

## Technical Details

### Cloudflare Custom Hostnames

When you create a Custom Hostname via API:
- Cloudflare creates an internal CNAME record (NOT visible to users)
- Cloudflare automatically issues SSL certificates
- Cloudflare handles all DNS routing internally
- No cross-account CNAME issues!

### API Call Example

```python
POST /zones/{zone_id}/custom_hostnames
{
    "hostname": "okmentor.in",
    "ssl": {
        "method": "http",
        "type": "dv"
    }
}

Response:
{
    "success": true,
    "result": {
        "id": "hostname_id_123",
        "hostname": "okmentor.in",
        "status": "pending",
        "ssl": {
            "status": "pending_validation",
            "validation_records": [...]
        }
    }
}
```

## Troubleshooting

### Issue: "Cloudflare credentials not configured"

**Solution**: Set environment variables:
```bash
CLOUDFLARE_API_TOKEN=xxx
CLOUDFLARE_ZONE_ID=xxx
CLOUDFLARE_ACCOUNT_ID=xxx
```

### Issue: "Error 1014" still appears

**Solution**: 
1. Stop adding manual CNAME records
2. Delete any manual CNAME records from Cloudflare
3. Use Custom Hostnames API instead (automatic)
4. Wait 5-10 minutes for DNS to propagate

### Issue: "Custom hostname creation failed"

**Solution**: Check:
1. Zone ID is correct (for nextslot.in, not provider's domain)
2. API token has Custom Hostnames permissions
3. API token is for YOUR account (nextslot.in account)
4. Custom Hostnames feature is enabled in Cloudflare dashboard

### Issue: Domain shows "pending" status

**Solution**: 
- This is normal! Cloudflare takes 5-30 minutes to fully activate
- SSL certificate is being issued
- Just wait for status to change to "active"

## Migration Steps (If Currently Using Manual CNAMEs)

If providers are already using manual CNAME records:

1. **Tell provider to delete their manual CNAME records**
   ```
   From registrar, delete:
   - Type: CNAME
   - Name: www (or @)
   - Target: customers.nextslot.in
   ```

2. **System creates Custom Hostname via API**
   ```bash
   python setup_cloudflare_custom_hostnames.py
   ```

3. **Wait 10-30 minutes**
   - Cloudflare processes the Custom Hostname
   - SSL certificate is issued
   - Domain becomes active

4. **Domain now works automatically!**
   - No manual CNAME needed
   - SSL is active
   - Error 1014 is gone!

## Benefits of Custom Hostnames

✅ **No Error 1014** - No cross-account CNAME issues  
✅ **Automatic SSL** - Certificates issued immediately  
✅ **Easy for providers** - No DNS configuration needed  
✅ **Scalable** - Add unlimited customer domains  
✅ **Automatic routing** - Cloudflare handles everything  
✅ **No manual CNAME records** - API-driven setup  

## What Providers See

### Before (Manual CNAME - Error 1014)
```
User visits: okmentor.in
  ↓
Browser tries to access website
  ↓
Error 1014: CNAME Cross-User Banned
  ↓
❌ Domain doesn't work!
```

### After (Custom Hostnames - Works!)
```
User visits: okmentor.in
  ↓
Cloudflare routes to app
  ↓
SSL certificate is valid
  ↓
Shows provider's booking page
  ↓
✓ Domain works perfectly!
```

## Summary

**The Fix:**
- Stop using manual CNAME records
- Use Cloudflare Custom Hostnames API instead
- It handles everything automatically
- Error 1014 is eliminated
- Providers get better experience

**Next Action:**
1. Set Cloudflare credentials in environment
2. Run: `python setup_cloudflare_custom_hostnames.py`
3. Delete any manual CNAME records from Cloudflare
4. Domains will be active in 5-30 minutes!
