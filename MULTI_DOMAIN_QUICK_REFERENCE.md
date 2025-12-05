# Multi-Domain System - Quick Reference

## 🎯 Overview

A complete multi-domain system allowing PRO users to manage unlimited custom domains with independent DNS configurations.

## 🚀 Quick Start

### 1. Add a Domain (Provider)
1. Go to `/providers/domains/` (Multi-Domain Dashboard)
2. Click **"Add New Domain"**
3. Enter domain name: `salon.com`
4. Select domain type: `Custom Domain` or `Subdomain`
5. Select DNS type: `CNAME` (recommended), `A Record`, or `Both`
6. Click **"Add Domain"**

### 2. Configure DNS Records
1. Copy the CNAME target: `app.nextslot.in`
2. Go to your domain registrar (GoDaddy, Namecheap, etc.)
3. Add DNS record:
   - **Type:** CNAME
   - **Name:** @ (or www)
   - **Value:** app.nextslot.in
   - **TTL:** 3600 (or Auto)
4. Click **"Save"**

### 3. Verify Domain
1. Wait 5-30 minutes for DNS propagation
2. Click **"Verify Domain"** in the setup page
3. System checks DNS configuration
4. If verified, domain becomes active

### 4. Set as Primary
1. Once domain is active, click **"Set as Primary"**
2. This becomes your main booking URL
3. Previous primary is now secondary

## 📋 Domain Status Lifecycle

```
pending          → Domain added, waiting for setup
    ↓
dns_configured   → DNS records added
    ↓
dns_verified     → DNS resolves correctly
    ↓
ssl_pending      → SSL certificate being generated
    ↓
ssl_active       → SSL certificate installed
    ↓
active           → Domain fully live! 🎉

OR

failed           → Setup encountered error
```

## 🔌 DNS Record Types

| Type | Format | When to Use |
|------|--------|------------|
| **CNAME** | `@ → app.nextslot.in` | Most registrars (Recommended) |
| **A Record** | `@ → 203.0.113.42` | If CNAME not available |
| **Both** | Both CNAME & A | Maximum compatibility |

## 📱 Key Pages & Routes

| Route | Purpose | Who Can Access |
|-------|---------|-----------------|
| `/providers/domains/` | Dashboard - see all domains | PRO users |
| `/providers/domains/add/` | Add new domain form | PRO users |
| `/providers/domains/<id>/setup/` | DNS setup instructions | PRO users |
| `/providers/domains/<id>/verify/` | Verify domain configuration | PRO users |
| `/providers/domains/<id>/manage/` | Manage single domain | PRO users |
| `/providers/domains/<id>/status/` | JSON status endpoint | PRO users |
| `/providers/domains/list/json/` | JSON list of all domains | PRO users |

## 🔑 Key Models & Functions

### CustomDomain Model
```python
domain = CustomDomain.objects.get(id=5)
domain.domain_name              # "salon.com"
domain.status                   # "active", "pending", etc.
domain.is_primary               # True/False
domain.ssl_enabled              # True/False
domain.verified_at              # DateTime
domain.ssl_expiry_date          # Date
domain.get_access_url()         # "https://salon.com"
domain.is_verified()            # True/False
domain.needs_renewal()          # True if < 30 days to expiry
```

### Key Functions

#### Create a Domain
```python
from providers.simple_dns import create_custom_domain_record

result = create_custom_domain_record(
    provider=provider,
    domain_name='salon.com',
    domain_type='custom'  # or 'subdomain'
)
# Returns: {success: bool, domain_id: int, instructions: dict}
```

#### Get All Domains
```python
from providers.simple_dns import get_provider_domains_summary

summary = get_provider_domains_summary(provider)
summary['primary_domain']       # Primary domain info
summary['active_domains']       # List of active domains
summary['pending_domains']      # Waiting for DNS
summary['failed_domains']       # Setup failed
summary['total_domains']        # Count
```

#### Verify a Domain
```python
from providers.simple_dns import verify_multi_domain

verification = verify_multi_domain(domain)
verification['verified']        # True/False
verification['ssl_enabled']     # True/False
verification['access_url']      # "https://salon.com"
```

#### Get DNS Instructions
```python
from providers.simple_dns import get_multi_domain_setup_instructions

instructions = get_multi_domain_setup_instructions(domain)
instructions['cname']['value']      # "app.nextslot.in"
instructions['cname']['ttl']        # 3600
instructions['txt_verification']   # Verification TXT record
```

#### Set Primary Domain
```python
from providers.simple_dns import set_primary_domain

set_primary_domain(domain)      # Removes primary from others
```

#### Delete Domain
```python
from providers.simple_dns import delete_custom_domain

result = delete_custom_domain(domain)
# Returns: {success: bool, message: str}
# Fails if domain is primary
```

## 📊 Dashboard Features

The multi-domain dashboard shows:
- 📈 Statistics (total, active, pending, failed domains)
- ⭐ Primary domain highlighted
- 🔧 Quick action buttons (manage, setup, verify, set-primary, remove)
- 🔐 SSL status indicator
- 📅 Added date and verification date
- 🌐 Domain type (custom/subdomain)
- 🎨 Color-coded status badges

## 🔒 Permissions & Access Control

- ✅ Providers must be PRO users
- ✅ Can only manage their own domains
- ✅ Cannot add duplicate domains
- ✅ Cannot delete primary domain
- ✅ Cannot set unverified domain as primary

## 🛡️ SSL Certificate Management

**Provider:** Let's Encrypt (FREE)

- ✅ Automatic SSL certificate generation
- ✅ Auto-renewal every 90 days
- ✅ No cost, no action required
- ✅ Expiry tracking in database
- ✅ Renewal alerts (if < 30 days)

## 📡 DNS Propagation

**Typical Timeline:**
- ⏱️ 5-30 minutes (usually)
- ⚠️ Can take up to 48 hours
- 🔍 Check status at: https://mxtoolbox.com

## 🆚 Supported Registrars

| Registrar | CNAME | A Record | Notes |
|-----------|-------|----------|-------|
| GoDaddy | ✅ | ✅ | Most common |
| Namecheap | ✅ | ✅ | Very reliable |
| AWS Route53 | ✅ | ✅ | Enterprise-grade |
| Google Domains | ✅ | ✅ | Simple interface |
| Bluehost | ✅ | ✅ | Hosting provider |
| HostGator | ✅ | ✅ | Hosting provider |
| Any registrar | ✅ | ✅ | Standard DNS |

## 🐛 Troubleshooting

### Domain not verifying?
1. Check DNS propagation at https://mxtoolbox.com
2. Wait 5-30 minutes and try again
3. Verify CNAME value is exactly `app.nextslot.in`
4. No http:// or https:// prefix needed

### SSL certificate not generating?
1. Wait 5-15 minutes after DNS verification
2. Check certificate status in domain manage page
3. Check admin notes for error details
4. Contact support if still failing

### Can't set as primary?
1. Domain must be in "active" status first
2. Complete DNS setup and verification
3. Generate SSL certificate
4. Then you can set as primary

### Domain disappeared?
1. Check if domain was accidentally deleted
2. Check if domain was marked inactive
3. Refresh page to see updated status
4. Check admin notes for deletion reasons

## 📈 Analytics & Monitoring

Track domain health:
- Total domains per provider
- Active vs pending domains
- Failed domain setups
- SSL certificate expiry dates
- DNS record types in use
- Verification success rates

## 🔗 API Integration Examples

### Get Domain Status (JavaScript)
```javascript
fetch('/providers/domains/5/status/')
    .then(r => r.json())
    .then(data => {
        console.log(data.domain)        // "salon.com"
        console.log(data.status)        // "active"
        console.log(data.ssl_enabled)   // true
        console.log(data.url)           // "https://salon.com"
    })
```

### Get All Domains (JavaScript)
```javascript
fetch('/providers/domains/list/json/')
    .then(r => r.json())
    .then(data => {
        console.log(data.total_domains)     // 3
        data.domains.forEach(d => {
            console.log(`${d.domain_name} - ${d.status}`)
        })
    })
```

## 🎓 Learning Resources

- 📖 Full documentation: `MULTI_DOMAIN_SYSTEM.md`
- 🔍 Check DNS: https://mxtoolbox.com/
- 📜 Let's Encrypt: https://letsencrypt.org/
- 🌐 DNS Basics: https://www.cloudflare.com/learning/dns/

## ⚡ Performance Tips

1. **Cache domain lookups** - Domains don't change frequently
2. **Use bulk operations** - When managing many domains
3. **Async verification** - Don't block on DNS checks
4. **Index queries** - Already indexed on status, domain_name
5. **Monitor SSL expiry** - Set reminders for renewals

## 📞 Support

- 🐛 Issues? Check admin notes in domain records
- 📧 Contact support@nextslot.in
- 💬 Check FAQ section in add domain form
- 📚 Refer to full documentation

---

**Last Updated:** December 5, 2024
**Version:** 1.0
**Status:** ✅ Production Ready
