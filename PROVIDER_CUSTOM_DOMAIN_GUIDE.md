# Service Provider: How to Use Your Custom Domain

## Overview

Your custom domain (like `okmentor.in`) is now fully automatic! No manual DNS configuration needed.

## Step-by-Step Setup

### 1. Tell Us Your Domain

Go to your booking dashboard → Settings → Custom Domain

Enter your domain: `okmentor.in` (or whatever domain you want)

Click: "Add Custom Domain"

**That's it!** The system now handles everything automatically.

### 2. What Happens Next

- ✅ System registers your domain in Cloudflare
- ✅ SSL certificate is automatically issued
- ✅ Your domain is configured to work with our app
- ⏱️ Takes 5-30 minutes (usually 10 minutes)

### 3. Wait a Bit

While Cloudflare is setting up:
- Status: "Pending" (this is normal!)
- You can check status in your dashboard
- Don't manually add any DNS records
- Don't change your domain settings

### 4. Your Domain Is Ready

Once status shows "Active":
- ✅ Your domain works!
- ✅ SSL is active (secure connection)
- ✅ Customers can visit your booking page
- ✅ Everything is automatic!

## What Your Customers See

When customers visit your domain (e.g., `www.okmentor.in`):

1. Browser connects to your domain
2. ✅ SSL certificate is valid (green lock)
3. ✅ Sees your booking page
4. ✅ Can make appointments!

## FAQ

### Q: Do I need to add any DNS records?

**No!** That's the beautiful part. Our system handles everything automatically using Cloudflare.

### Q: How long does it take to work?

Usually **10-30 minutes**. In rare cases, up to 1 hour.

### Q: Can I check the status?

Yes! Go to your dashboard → Settings → Custom Domain

You'll see:
- "Pending" = Still setting up (wait a bit)
- "Active" = Ready to use!

### Q: What if it says "Error 1014"?

Don't worry! This means Cloudflare is still setting things up.

**What to do:**
1. Wait 15 minutes
2. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)
3. Try again

If still not working after 30 minutes, contact support.

### Q: Can I remove my custom domain?

Yes, go to Settings → Custom Domain → Remove

The system will delete it from Cloudflare automatically.

### Q: Can I change my custom domain?

Yes! Remove the current one, then add a new one.

### Q: Is SSL (HTTPS) included?

Yes! SSL is automatic and included with your domain.

You'll see a green lock 🔒 in the browser.

### Q: Can I use a subdomain (like `book.okmentor.in`)?

Yes! Just enter the subdomain when adding your custom domain.

### Q: Does my domain need to be with any specific registrar?

No! You can use any registrar (GoDaddy, Namecheap, Google Domains, etc.)

The domain just needs to be registered and accessible.

### Q: What if I'm having issues?

**Try these steps:**

1. **Wait 30 minutes** - Cloudflare takes time to setup
2. **Hard refresh browser** - Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
3. **Clear browser cache** - Or use private/incognito mode
4. **Check status in dashboard** - Make sure it shows "Active"
5. **Contact support** - If it still doesn't work

## Support

If you have any issues:

- **Email:** support@nextslot.in
- **Chat:** Available in your dashboard
- **Response time:** Usually within 24 hours

**Include in your message:**
- Your domain name
- The status you see in dashboard
- When you added the domain
- What error you're seeing (if any)

## Technical Details (For IT/Developers)

Your domain is managed through **Cloudflare Custom Hostnames**.

- **SSL Certificate**: Automatic DV (Domain Validated)
- **Update frequency**: Real-time
- **Backup**: DigitalOcean App Platform
- **CDN**: Cloudflare global network
- **Uptime**: 99.99%

Your custom domain traffic flow:

```
Your domain (okmentor.in)
    ↓
Cloudflare (automatic routing & SSL)
    ↓
Our app (nextslot-app.ondigitalocean.app)
    ↓
Database (PostgreSQL)
    ↓
Your booking page!
```

## Billing

Custom domains are included in your plan!

- **Free plan**: No custom domains
- **Starter plan**: 1 custom domain
- **Professional plan**: 5 custom domains
- **Enterprise**: Unlimited custom domains

## Security

Your domain is secure:
- ✅ SSL/HTTPS encrypted
- ✅ Cloudflare DDoS protection
- ✅ Automatic backups
- ✅ PCI DSS compliant

## Advanced Options

Want more control? Contact support for:
- Custom SSL certificates
- Advanced routing rules
- Domain forwarding
- Email routing (with your domain)

---

**Questions?** Contact support or check our help center at:
https://nextslot.in/help/custom-domains
