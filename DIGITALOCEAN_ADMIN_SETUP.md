# DigitalOcean Admin Configuration Guide

## What You Need to Do (One-Time Setup)

This guide is for the admin/owner of the DigitalOcean account. Providers don't need to do this.

## Step 1: Deploy App to DigitalOcean

### Create DigitalOcean App

1. Go to: https://cloud.digitalocean.com/apps
2. Click: "Create" → "App"
3. Connect your GitHub repository
4. Select your main branch
5. Configure:
   - **App Name**: booking-saas (or similar)
   - **Source Component**: Python (Django)
   - **Port**: 8000
6. Add Environment Variables (from `.env` file):
   ```
   DEBUG=False
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgresql://...
   DEFAULT_DOMAIN=nextslot.in
   DIGITALOCEAN_APP_DOMAIN=your-app-XXXXXX.ondigitalocean.app
   ```
7. Click: "Create App"

### Get Your App Domain

After deployment completes:

1. Go to: Apps → Your App → Settings
2. Look for: "App Domain"
3. Copy the domain (e.g., `booking-saas-abc123.ondigitalocean.app`)
4. Update Django settings:

```python
# booking_saas/settings.py
DIGITALOCEAN_APP_DOMAIN = 'booking-saas-abc123.ondigitalocean.app'
```

## Step 2: Configure Your Main Domain (nextslot.in)

### At Your Domain Registrar

Add these DNS records for **nextslot.in**:

```
Record Type     Name        Value
──────────────  ─────────   ──────────────────────────────
CNAME           *           booking-saas-abc123.ondigitalocean.app
CNAME           www         booking-saas-abc123.ondigitalocean.app
A               @           203.0.113.42  # Your DigitalOcean IP
A               www         203.0.113.42
MX              (if needed) mail settings
```

**Explanation:**
- `*.nextslot.in` → All subdomains go to your DigitalOcean app
- This allows `okmentor.nextslot.in`, `ramesh.nextslot.in`, etc.

### In DigitalOcean Dashboard

1. Apps → Your App → Settings
2. Custom Domains section
3. Add:
   - `nextslot.in`
   - `www.nextslot.in`
4. DigitalOcean will:
   - Verify domain ownership
   - Generate SSL certificate via Let's Encrypt
   - Set up HTTPS for main domain

## Step 3: Configure SSL/HTTPS

### Enable Automatic HTTPS

In Django settings:

```python
# booking_saas/settings.py

# Force all traffic to HTTPS
SECURE_SSL_REDIRECT = not DEBUG  # True in production

# Trust DigitalOcean's SSL proxy headers
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Additional security headers
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
```

### Expected Result

- `http://nextslot.in` → Redirects to `https://nextslot.in`
- `http://okmentor.nextslot.in` → Redirects to `https://okmentor.nextslot.in`
- SSL certificates auto-generated for all subdomains and custom domains

## Step 4: Database Configuration

### Set up PostgreSQL

1. Go to: https://cloud.digitalocean.com/databases
2. Click: "Create Database"
3. Select:
   - **Engine**: PostgreSQL
   - **Version**: 14+ (latest)
   - **Region**: Same as your app (for speed)
4. After creation:
   - Copy connection string
   - Update Django: `DATABASE_URL` environment variable
5. Run migrations:
   ```bash
   python manage.py migrate
   ```

## Step 5: Test Everything

### Check App Status

1. Apps → Your App
2. Status should show: "Running" ✅

### Test Main Domain

1. Visit: `https://nextslot.in`
2. Check:
   - [ ] Green lock icon (SSL working)
   - [ ] Landing page loads
   - [ ] No security warnings

### Test Subdomain

1. Have a provider set up custom domain first
2. Visit: `https://provider-slug.nextslot.in`
3. Check:
   - [ ] Green lock icon
   - [ ] Provider's booking page loads
   - [ ] No HTTPS errors

### Test Custom Domain

After provider sets up their domain:

1. Visit: `https://provider-custom-domain.com`
2. Check:
   - [ ] Green lock icon
   - [ ] Provider's booking page loads
   - [ ] Same content as subdomain

## Step 6: Enable Custom Domains for Providers

### In Django Admin

1. Go to: `/admin/`
2. Select: Providers → Service Provider
3. For each provider, set:
   - **custom_domain**: Their domain (e.g., `okmentor.in`)
   - **custom_domain_type**: 'domain'
   - **has_pro_features**: True (if they have PRO subscription)

### Provide Setup Instructions

Send each provider:
- Custom domain setup URL on your app
- Or send them: `FIX_OKMENTOR_HTTPS.md`

## Step 7: Monitor and Maintain

### Monitor App Health

Weekly:
1. Check: Apps → Your App → Logs
2. Look for: Errors, crashes, performance issues
3. Monitor: Database usage, app resources

### Monitor SSL Certificates

Monthly:
1. Go to: DigitalOcean → Apps → Your App → Settings
2. Check: Custom Domains section
3. Status should show:
   - ✅ Verified for each domain
   - ✅ SSL Certificate (Let's Encrypt)

### Automatic SSL Renewal

DigitalOcean automatically renews certificates 30 days before expiry.

**You don't need to do anything** - it's automatic.

## Troubleshooting

### App Won't Start

1. Check: Logs → Deployment logs
2. Common issues:
   - Missing environment variables
   - Database connection error
   - Python dependency missing

**Fix**: Update environment variables or requirements.txt, then redeploy

### Domain Shows 404 Error

1. Check: CustomDomainMiddleware is enabled in settings
2. Check: ALLOWED_HOSTS contains the domain
3. Verify: Provider custom_domain is set in database

**Fix**: Make sure middleware is in MIDDLEWARE list in settings

### SSL Certificate Not Generated

1. Check: DNS records point to DigitalOcean
2. Check: DigitalOcean dashboard shows domain as "Active"
3. Wait: May take 5-30 minutes after domain addition

**Fix**: Remove and re-add domain to DigitalOcean

### Slow Performance

1. Upgrade app resources in DigitalOcean
2. Scale to multiple instances (load balancing)
3. Optimize database queries
4. Enable caching (Redis)

## Backup and Recovery

### Regular Backups

1. Database:
   - DigitalOcean automatically backs up PostgreSQL
   - Download backups monthly

2. Media Files:
   - If using DigitalOcean Spaces (CDN), backups automatic
   - Or set up periodic S3 backups

### Disaster Recovery

If everything fails:

1. **Restore Database**
   ```bash
   psql -h host -U user -d database < backup.sql
   ```

2. **Redeploy App**
   ```bash
   git push origin main
   # DigitalOcean auto-deploys from GitHub
   ```

3. **Restore Media Files**
   - If in Spaces: Automatic
   - If local: Re-upload or restore from backup

## Cost Optimization

### DigitalOcean Pricing Example

| Component | Size | Cost |
|-----------|------|------|
| App Platform | Basic ($5-12/mo) | ~$12 |
| Database | Starter ($15/mo) | ~$15 |
| Spaces (CDN) | 250GB ($5/mo) | ~$5 |
| **Monthly Total** | | **~$32** |

### Ways to Reduce Costs

- Start on smaller app size, scale up if needed
- Use Spaces only if > 1GB files
- Archive old appointment records monthly
- Use DigitalOcean's free tier for testing

## Scaling to Multiple Providers

Your system supports unlimited providers:

| Component | Support | Notes |
|-----------|---------|-------|
| Providers | Unlimited | Each gets own subdomain |
| Custom Domains | Unlimited | Each provider can have 1+ |
| SSL Certificates | Unlimited | Auto-generated per domain |
| Bandwidth | See tier | Scale app if needed |
| Database | See tier | Upgrade if > 1000 providers |

## Security Best Practices

1. **Keep Updated**
   - Update Django regularly
   - Monitor security advisories

2. **Use Environment Variables**
   - Never commit secrets to GitHub
   - Use DigitalOcean's secret management

3. **Enable Monitoring**
   - Set up error alerts
   - Monitor database size
   - Track app resource usage

4. **Regular Audits**
   - Check access logs
   - Review Django admin access
   - Monitor payment transactions

## Support and Resources

- **DigitalOcean Docs**: https://docs.digitalocean.com/
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Let's Encrypt**: https://letsencrypt.org/
- **PostgreSQL Docs**: https://www.postgresql.org/docs/

## Next Steps

1. ✅ Deploy app to DigitalOcean
2. ✅ Configure main domain (nextslot.in)
3. ✅ Set up SSL certificates
4. ✅ Test everything works
5. ✅ Enable providers to add custom domains
6. ✅ Monitor and maintain

You're all set! Providers can now:
- Add their custom domains
- Get automatic SSL certificates
- Use independent booking pages

---

## Quick Checklist

- [ ] App deployed to DigitalOcean
- [ ] App domain obtained (e.g., app.ondigitalocean.app)
- [ ] DIGITALOCEAN_APP_DOMAIN set in Django settings
- [ ] Main domain (nextslot.in) DNS records added
- [ ] Main domain added to DigitalOcean custom domains
- [ ] SECURE_SSL_REDIRECT = True in settings
- [ ] Database connected and working
- [ ] Migrations run successfully
- [ ] Admin access working at /admin/
- [ ] Test domain loads with HTTPS
- [ ] Providers can access custom domain setup page
- [ ] Documentation sent to first provider
- [ ] Monitor app logs regularly

Once all boxes checked, your system is ready for production!
