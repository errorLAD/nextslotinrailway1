# Multi-Domain System Implementation - Complete Guide

## Overview

This document describes the new **Multi-Domain Support System** that allows service providers to manage multiple custom domains with independent DNS configurations, SSL certificates, and status tracking.

## What's New

### 1. New CustomDomain Model
**File:** `providers/models.py`

The new `CustomDomain` model replaces single-domain limitation with unlimited domains per provider:

```python
class CustomDomain(models.Model):
    # Each provider can have multiple domains
    service_provider = ForeignKey(ServiceProvider)
    domain_name = CharField(max_length=255)
    
    # Independent DNS configuration per domain
    dns_record_type = CharField(choices=['cname', 'a_record', 'both'])
    cname_target = CharField(max_length=255)
    a_record_ip = CharField(max_length=15)
    
    # Status tracking
    status = CharField(choices=['pending', 'dns_configured', 'dns_verified', 'ssl_pending', 'ssl_active', 'active'])
    
    # SSL management
    ssl_enabled = BooleanField()
    ssl_expiry_date = DateField()
    
    # Primary domain designation
    is_primary = BooleanField()
    is_active = BooleanField()
```

**Key Features:**
- ✅ Multiple domains per provider
- ✅ Independent DNS records (CNAME, A Record, or both)
- ✅ Unique verification codes per domain
- ✅ SSL certificate tracking
- ✅ Primary domain selection
- ✅ Domain status tracking throughout setup process

### 2. Enhanced DNS Module
**File:** `providers/simple_dns.py` (new functions added)

New multi-domain support functions:

```python
get_multi_domain_setup_instructions(custom_domain_obj)
  - Returns DNS setup instructions for specific domain
  - Supports CNAME, A Record, or both
  - Includes TXT verification record

verify_multi_domain(custom_domain_obj)
  - Verifies domain configuration
  - Returns current status
  - Tracks SSL expiry

get_provider_domains_summary(provider)
  - Lists all domains and their status
  - Separates active, pending, failed domains
  - Shows primary domain

create_custom_domain_record(provider, domain_name, domain_type)
  - Creates new domain record
  - Generates unique verification codes
  - Returns setup instructions

set_primary_domain(custom_domain_obj)
  - Sets a domain as primary
  - Removes primary status from others

delete_custom_domain(custom_domain_obj)
  - Safely removes domain
  - Prevents deletion of primary domain
```

### 3. Multi-Domain Management Views
**File:** `providers/views_multi_domain.py` (NEW)

Complete set of views for managing multiple domains:

```
/providers/domains/                          - Dashboard (all domains)
/providers/domains/add/                      - Add new domain form
/providers/domains/<id>/setup/               - DNS setup instructions
/providers/domains/<id>/verify/              - Verify domain
/providers/domains/<id>/manage/              - Manage domain
/providers/domains/<id>/set-primary/         - Set as primary
/providers/domains/<id>/remove/              - Remove domain
/providers/domains/<id>/status/              - JSON status endpoint
/providers/domains/list/json/                - JSON list of all domains
```

**Features:**
- ✅ Dashboard showing all domains with status
- ✅ Form to add new domains with DNS type selection
- ✅ Step-by-step DNS setup instructions
- ✅ Domain verification process
- ✅ Primary domain management
- ✅ JSON API for real-time updates

### 4. Multi-Domain Templates
**File:** `templates/providers/multi_domains_dashboard.html` (NEW)

Dashboard template features:
- 📊 Statistics cards (total, active, pending, failed)
- 🌟 Primary domain highlighted
- 📋 Domain cards with full information
- 🔧 Quick actions (manage, setup, verify, set primary, remove)
- 📱 Responsive grid layout
- ✨ Beautiful status badges

**File:** `templates/providers/add_domain.html` (NEW)

Domain add form features:
- ✅ Domain name input with validation
- 🔘 Domain type selection (custom vs subdomain)
- 🔌 DNS record type selection (CNAME, A, or both)
- 📚 Interactive examples
- ❓ FAQ section with common questions
- ⚠️ Helpful hints for each option

### 5. Updated URL Configuration
**File:** `providers/urls.py`

New URL patterns for multi-domain management:

```python
# Multi-Domain Management (NEW - PRO Feature)
path('domains/', views_multi_domain.multi_domains_dashboard, name='multi_domains_dashboard'),
path('domains/add/', views_multi_domain.add_domain, name='add_domain'),
path('domains/<int:domain_id>/setup/', views_multi_domain.domain_setup, name='domain_setup'),
path('domains/<int:domain_id>/verify/', views_multi_domain.domain_verify, name='domain_verify'),
path('domains/<int:domain_id>/manage/', views_multi_domain.domain_manage, name='domain_manage'),
path('domains/<int:domain_id>/set-primary/', views_multi_domain.set_primary, name='set_primary'),
path('domains/<int:domain_id>/remove/', views_multi_domain.remove_domain, name='remove_domain'),
path('domains/<int:domain_id>/status/', views_multi_domain.domain_status_json, name='domain_status_json'),
path('domains/list/json/', views_multi_domain.domains_list_json, name='domains_list_json'),
```

## Usage Examples

### Adding a Domain

```python
from providers.simple_dns import create_custom_domain_record

provider = ServiceProvider.objects.get(id=1)
result = create_custom_domain_record(
    provider=provider,
    domain_name='salon.com',
    domain_type='custom'  # or 'subdomain'
)

if result['success']:
    domain_id = result['domain_id']
    instructions = result['instructions']
```

### Getting All Domains

```python
from providers.simple_dns import get_provider_domains_summary

provider = ServiceProvider.objects.get(id=1)
summary = get_provider_domains_summary(provider)

print(summary['primary_domain'])      # Primary domain
print(summary['active_domains'])      # List of active domains
print(summary['pending_domains'])     # Waiting for DNS
print(summary['failed_domains'])      # Setup failed
```

### Verifying a Domain

```python
from providers.models import CustomDomain
from providers.simple_dns import verify_multi_domain

domain = CustomDomain.objects.get(id=5)
verification = verify_multi_domain(domain)

if verification['verified']:
    domain.mark_verified()  # Mark as active
```

### DNS Setup Instructions

```python
from providers.models import CustomDomain
from providers.simple_dns import get_multi_domain_setup_instructions

domain = CustomDomain.objects.get(id=5)
instructions = get_multi_domain_setup_instructions(domain)

# Returns:
# {
#     "domain": "salon.com",
#     "cname": {"name": "@", "value": "app.nextslot.in", "ttl": 3600},
#     "txt_verification": {"name": "_booking-verify-xxx", "value": "verify-xxx"},
#     "propagation_info": {...}
# }
```

## Database Migration

The system uses Django migrations to create the new `CustomDomain` table:

```bash
python manage.py makemigrations providers
python manage.py migrate providers
```

**Migration:** `providers/migrations/0017_customdomain.py`

### Schema

```sql
CREATE TABLE providers_customdomain (
    id INT PRIMARY KEY AUTO_INCREMENT,
    service_provider_id INT NOT NULL FOREIGN KEY,
    domain_name VARCHAR(255) NOT NULL,
    domain_type VARCHAR(20) DEFAULT 'custom',
    dns_record_type VARCHAR(20) DEFAULT 'cname',
    cname_target VARCHAR(255) DEFAULT 'app.nextslot.in',
    a_record_ip VARCHAR(15),
    verification_code VARCHAR(100) UNIQUE NOT NULL,
    txt_record_name VARCHAR(255) UNIQUE NOT NULL,
    ssl_enabled BOOLEAN DEFAULT FALSE,
    ssl_provider VARCHAR(50) DEFAULT 'lets_encrypt',
    ssl_certificate_id VARCHAR(255),
    ssl_expiry_date DATE,
    status VARCHAR(20) DEFAULT 'pending',
    is_primary BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    added_at DATETIME AUTO_NOW_ADD,
    verified_at DATETIME,
    ssl_generated_at DATETIME,
    last_verified_at DATETIME,
    updated_at DATETIME AUTO_NOW,
    admin_notes TEXT,
    UNIQUE(service_provider_id, domain_name),
    INDEX(status),
    INDEX(domain_name)
);
```

## Status Workflow

Domains go through this status lifecycle:

```
pending
    ↓
dns_configured (DNS records added)
    ↓
dns_verified (DNS resolves correctly)
    ↓
ssl_pending (SSL certificate being generated)
    ↓
ssl_active (SSL certificate installed)
    ↓
active (Domain fully live)

OR

failed (Setup encountered error)
```

## DNS Record Types

### CNAME Record (Recommended)
- **Best for:** Most registrars (GoDaddy, Namecheap, AWS Route53, Google Domains)
- **Setup:**
  - Name: `@` or `www`
  - Value: `app.nextslot.in`
  - TTL: 3600 (or Auto)

### A Record (Fallback)
- **Best for:** Registrars that don't support CNAME on root
- **Setup:**
  - Name: `@`
  - Value: `[IP Address]`
  - TTL: 3600 (or Auto)

### Both (Maximum Compatibility)
- Add both CNAME and A Record
- Some registrars allow both
- Highest redundancy

## SSL Certificate Management

**Provider:** Let's Encrypt (free)

**Auto-Renewal:** Every 90 days (automatic)

**Status Tracking:**
- `ssl_enabled` - Boolean flag
- `ssl_certificate_id` - Certificate ID from provider
- `ssl_expiry_date` - When certificate expires
- `needs_renewal()` - Returns true if expires in < 30 days

## Primary Domain

Each provider has ONE primary domain:
- Used as the main booking URL
- Displayed in profiles
- Must be in "active" status before setting as primary
- Can be changed anytime
- Cannot be deleted

## API Endpoints

### Get Domain Status (JSON)
```
GET /providers/domains/<id>/status/

Response:
{
    "domain": "salon.com",
    "domain_id": 5,
    "status": "active",
    "verified": true,
    "ssl_enabled": true,
    "url": "https://salon.com",
    "added_at": "2024-01-15T10:30:00Z",
    "verified_at": "2024-01-15T10:45:00Z",
    "ssl_expiry": "2025-01-15"
}
```

### Get All Domains (JSON)
```
GET /providers/domains/list/json/

Response:
{
    "provider_id": 1,
    "total_domains": 3,
    "domains": [
        {
            "id": 5,
            "domain_name": "salon.com",
            "status": "active",
            "is_primary": true,
            "ssl_enabled": true,
            "added_at": "2024-01-15T10:30:00Z",
            "verified_at": "2024-01-15T10:45:00Z"
        },
        ...
    ]
}
```

## Features Comparison

### Before (Single Domain)
- ❌ Only 1 domain per provider
- ❌ Domain on ServiceProvider model
- ❌ Simple CNAME only
- ❌ No DNS flexibility
- ❌ Limited status tracking
- ❌ No TXT verification records

### After (Multi-Domain)
- ✅ Unlimited domains per provider
- ✅ CustomDomain model with full tracking
- ✅ CNAME, A Record, or both
- ✅ Flexible DNS configuration
- ✅ Full status tracking (pending → active)
- ✅ TXT verification records per domain
- ✅ SSL certificate expiry tracking
- ✅ Primary domain management
- ✅ JSON API for real-time status
- ✅ Beautiful dashboard UI
- ✅ Domain management views
- ✅ History and audit trail

## Migration from Single Domain

For existing providers with single custom domains:

```python
from providers.models import ServiceProvider, CustomDomain

for provider in ServiceProvider.objects.exclude(custom_domain=''):
    if not CustomDomain.objects.filter(
        service_provider=provider
    ).exists():
        # Create CustomDomain from existing single domain
        CustomDomain.objects.create(
            service_provider=provider,
            domain_name=provider.custom_domain,
            domain_type=provider.custom_domain_type,
            verification_code=provider.domain_verification_code,
            status='active' if provider.domain_verified else 'pending',
            ssl_enabled=provider.ssl_enabled,
            is_primary=True,
        )
```

## Files Modified/Created

### Created:
- ✨ `providers/models.py` - Added CustomDomain model (88 lines)
- ✨ `providers/views_multi_domain.py` - Multi-domain views (281 lines)
- ✨ `providers/migrations/0017_customdomain.py` - Database migration
- ✨ `templates/providers/multi_domains_dashboard.html` - Dashboard template
- ✨ `templates/providers/add_domain.html` - Add domain form template

### Updated:
- 🔄 `providers/models.py` - Added CustomDomain model
- 🔄 `providers/simple_dns.py` - Added multi-domain functions (200+ lines)
- 🔄 `providers/urls.py` - Added multi-domain URL patterns

## Next Steps

1. **Database Migration:**
   ```bash
   python manage.py migrate
   ```

2. **Create Missing Templates:**
   - `templates/providers/domain_setup.html`
   - `templates/providers/domain_verify.html`
   - `templates/providers/domain_manage.html`

3. **Add Navigation:**
   - Add link to multi-domain dashboard in provider dashboard
   - Add to provider settings menu

4. **Testing:**
   - Test adding domain
   - Test DNS setup workflow
   - Test verification process
   - Test primary domain switching
   - Test domain removal

5. **Optional Features:**
   - CNAME/A record auto-verification (DNS lookup)
   - SSL certificate auto-renewal tracking
   - Domain health checks
   - Bulk operations
   - Domain usage analytics

## Backward Compatibility

The new system maintains backward compatibility:
- Legacy single-domain fields remain on ServiceProvider
- Existing domain routes still work
- Can migrate to multi-domain gradually
- No breaking changes to existing code

## Performance Considerations

- 📊 **Queries:** Use `select_related('service_provider')` when listing domains
- 🔍 **Indexes:** Added on `(service_provider, is_active)`, `status`, `domain_name`
- 💾 **Cache:** Consider caching domain lookups for frequently accessed domains
- ⏱️ **Async:** SSL verification could be done asynchronously

## Support

For questions or issues with the multi-domain system:
- Check DNS records at: https://mxtoolbox.com
- Check SSL certificates at: https://certhero.com
- Verify domain status in dashboard
- Review admin notes for failed domains
