# Fix okmentor.in HTTPS Error - Quick Action Guide

## Your Problem

You visit `https://okmentor.in` and see:
```
"doesn't support a secure connection with HTTPS"
```

## Root Cause

The SSL certificate for okmentor.in hasn't been provisioned yet because one or more of these is missing:

1. DNS record not added/propagated
2. Domain not registered in DigitalOcean
3. Let's Encrypt still processing (takes 5-30 min)
4. Wrong CNAME target

## Immediate Actions (Do These NOW)

### Action 1: Verify DNS is Set Correctly

Go to your registrar (GoDaddy, Namecheap, Route53, etc.) and check:

**DNS Record for okmentor.in should be:**

```
Name/Host:  @ (or root)
Type:       CNAME
Points To:  okmentor.nextslot.in
TTL:        3600
```

✅ **If this is set correctly**, go to Action 2

❌ **If missing or wrong**, fix it now:
- Log in to your registrar
- Find "Manage DNS" or "Edit DNS Records"
- Add/Update CNAME record
- Save changes
- Wait 5-30 minutes for propagation

### Action 2: Verify DNS Propagation

Open https://mxtoolbox.com/cname/okmentor.in

**You should see:**
```
okmentor.in → okmentor.nextslot.in
```

✅ **If shows this**, go to Action 3

❌ **If shows something else or "Not found"**:
- DNS is still propagating (normal, wait 15-30 min)
- Or DNS record is still wrong (go back to Action 1)

### Action 3: Add Domain to DigitalOcean

1. Go to: https://cloud.digitalocean.com/apps
2. Click: Your App name
3. Go to: "Settings" tab
4. Find: "Custom Domains" section
5. Click: "Edit" button
6. Click: "Add Domain"
7. Type: `okmentor.in`
8. Click: "Save"

DigitalOcean will:
- Verify the domain
- Request SSL certificate from Let's Encrypt
- Generate certificate (5-30 minutes)

### Action 4: Wait for SSL Certificate

After adding domain to DigitalOcean:

- **After 5 minutes**: Check domain status in DigitalOcean (should show progress)
- **After 15 minutes**: Try visiting `https://okmentor.in` again
- **After 30 minutes**: If still not working, do Action 5

### Action 5: Test in Browser

1. Open new incognito window (Ctrl+Shift+N)
2. Visit: `https://okmentor.in` (not http, must be https)
3. Check address bar:
   - ✅ Green lock icon = SSL working
   - ❌ No lock = Still not ready

## If Still Not Working After 1 Hour

Do these manual fixes:

### Fix Option A: Remove and Re-add Domain

In DigitalOcean:

1. Apps → Your App → Settings
2. Click "Edit" on Custom Domains
3. Find `okmentor.in`
4. Click "Remove"
5. Wait 5 minutes
6. Click "Add Domain" again
7. Add `okmentor.in`
8. Wait 30 minutes for certificate

### Fix Option B: Check Your App is Running

1. Go to: https://cloud.digitalocean.com/apps
2. Click: Your App
3. Check status (should say "Running" in green)
4. If not running, click "Run" to restart

### Fix Option C: Double-Check DNS (Advanced)

Open command prompt and run:

```bash
nslookup okmentor.in
# Should return: okmentor.nextslot.in

nslookup okmentor.nextslot.in  
# Should return: app.ondigitalocean.app
```

If output is different:
- Go back to Action 1 and check registrar DNS
- Wait more time for propagation

## Network Bypass (Workaround, Temporary)

If you're having temporary DNS issues, you can manually add to your hosts file:

**Windows:**
1. Open: `C:\Windows\System32\drivers\etc\hosts` (as Admin)
2. Add this line: `203.0.113.42 okmentor.in`
3. Save
4. Open browser, try `https://okmentor.in`

**Mac/Linux:**
1. Open Terminal
2. Run: `sudo nano /etc/hosts`
3. Add: `203.0.113.42 okmentor.in`
4. Save (Ctrl+O, then Ctrl+X)

⚠️ **This is temporary** - Remove after SSL is working

## Expected Timeline

| Time | Status | Action |
|------|--------|--------|
| Right now | Error | Your current situation |
| +5 min | DNS propagating | Wait, check at mxtoolbox |
| +15 min | DigitalOcean processing | Adding domain to app |
| +30 min | Certificate generating | Let's Encrypt working |
| +45 min | Should be working | Try https://okmentor.in |
| +1 hour | If still broken | Do manual fixes above |

## Verify It's Actually Working

Once green lock appears:

1. Visit: `https://okmentor.in`
2. Check:
   - [ ] Green lock icon in address bar
   - [ ] Page loads your booking page
   - [ ] No browser warnings
   - [ ] Address bar shows `https://` (not http://)
   - [ ] Certificate shows Let's Encrypt in details

## Certificate Details (What to Expect)

Right-click address bar → inspect certificate:

```
Issued by: Let's Encrypt (FREE)
Subject: okmentor.in
Valid: Usually 90 days
Auto-renews: Every 60 days (automatic, you do nothing)
```

## Quick Checklist

Before declaring success:

- [ ] DNS CNAME record added at registrar
- [ ] DNS propagated (verified at mxtoolbox)
- [ ] Domain added to DigitalOcean app settings
- [ ] Wait 30+ minutes
- [ ] Green lock icon showing
- [ ] Certificate from Let's Encrypt
- [ ] https://okmentor.in loads booking page
- [ ] No browser security warnings

## If Multiple Providers Need This

Each provider repeats this process for their domain:

| Provider | Custom Domain | Provider Subdomain | Action |
|----------|----------------|-------------------|--------|
| okmentor | okmentor.in | okmentor.nextslot.in | Add CNAME in registrar |
| Ramesh | ramesh-salon.com | ramesh-salon.nextslot.in | Add CNAME in registrar |
| John | john-fitness.com | john-fitness.nextslot.in | Add CNAME in registrar |

Each gets their own Let's Encrypt SSL certificate automatically.

## Support Resources

- **DNS Check**: https://mxtoolbox.com/cname/
- **SSL Test**: https://www.ssllabs.com/ssltest/
- **DigitalOcean Help**: https://docs.digitalocean.com/products/app-platform/
- **Let's Encrypt**: https://letsencrypt.org/

## Emergency Contact

If this guide doesn't fix it:

1. Email: support@nextslot.in (describe what you did)
2. Include:
   - Your domain name
   - Screenshot of error
   - DNS record you added
   - When you added it

---

## TL;DR (Ultra Quick Version)

1. Add CNAME record: `okmentor.in` → `okmentor.nextslot.in` at your registrar
2. Wait 15 minutes for DNS to propagate
3. Go to DigitalOcean → Apps → Your App → Settings → Custom Domains → Add `okmentor.in`
4. Wait 30 minutes
5. Visit `https://okmentor.in` (should show green lock)
6. Done!

If not working after 1 hour, remove and re-add domain to DigitalOcean.
