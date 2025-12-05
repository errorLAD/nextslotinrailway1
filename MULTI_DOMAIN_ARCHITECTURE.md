# Multi-Domain Architecture Diagram

## System Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         NEXTSLOT MULTI-DOMAIN SYSTEM                   │
└────────────────────────────────────────────────────────────────────────┘

                              Internet Users
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
              okmentor.in    salon.nextslot.in  nextslot.in
              (Custom)      (Subdomain)        (Main App)
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                        ┌───────────▼────────────┐
                        │ Cloudflare for SaaS    │
                        │ (SSL + DNS)            │
                        └───────────┬────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Fallback Domain               │
                    │ customers.nextslot.in         │
                    └───────────────┬───────────────┘
                                    │
                        ┌───────────▼────────────┐
                        │ Railway App Server     │
                        │ (Django Application)   │
                        └───────────┬────────────┘
                                    │
                    ┌───────────────▼────────────┐
                    │ CustomDomainMiddleware      │
                    │ - Detect domain/host       │
                    │ - Find provider in DB      │
                    │ - Route to booking page    │
                    └───────────────┬────────────┘
                                    │
                    ┌───────────────▼────────────┐
                    │ Provider Booking Page       │
                    │ /appointments/book/{slug}/ │
                    └────────────────────────────┘
```

---

## Request Flow - Step by Step

### Scenario 1: Accessing Custom Domain (okmentor.in)

```
Step 1: User Request
────────────────────
GET https://okmentor.in/
Host: okmentor.in

Step 2: DNS Resolution
──────────────────────
okmentor.in → customers.nextslot.in (CNAME record)

Step 3: Cloudflare Processing
──────────────────────────────
URL: okmentor.in
Cloudflare intercepts
SSL Certificate: Active ✓
Route to fallback: customers.nextslot.in

Step 4: Railway App Receives
────────────────────────────
Host Header: okmentor.in
Path: /
Query: (none)

Step 5: CustomDomainMiddleware
──────────────────────────────
1. Extract host: okmentor.in
2. Check if custom domain: YES
3. Query DB: ServiceProvider.objects.get(custom_domain='okmentor.in')
4. Result: Provider "Anju Mishra" found ✓
5. Set request.custom_domain_provider = provider
6. Request path is "/": YES → Redirect

Step 6: Redirect
────────────────
Redirect to: /appointments/book/anju-mishra/
Status: 302 Found

Step 7: User Sees
─────────────────
URL: https://okmentor.in/ (unchanged)
Content: Anju Mishra's booking page
```

### Scenario 2: Accessing Subdomain (salon.nextslot.in)

```
Step 1: User Request
────────────────────
GET https://salon.nextslot.in/
Host: salon.nextslot.in

Step 2: Cloudflare
──────────────────
SSL Certificate: Active ✓ (wildcard *.nextslot.in)

Step 3: CustomDomainMiddleware
──────────────────────────────
1. Extract host: salon.nextslot.in
2. Check if subdomain of nextslot.in: YES
3. Extract subdomain: salon
4. Query DB: ServiceProvider.objects.get(unique_booking_url='salon', is_active=True)
5. Result: Provider "Beauty Salon" found ✓
6. Set request.custom_domain_provider = provider
7. Request path is "/": YES → Redirect

Step 4: Redirect
────────────────
Redirect to: /appointments/book/beauty-salon/
Status: 302 Found

Step 5: User Sees
─────────────────
URL: https://salon.nextslot.in/ (unchanged)
Content: Beauty Salon's booking page
```

---

## Database Schema Relationships

```
┌──────────────────────────────┐
│   ServiceProvider Model      │
├──────────────────────────────┤
│ id (PK)                      │
│ user_id (FK → User)          │
│ business_name                │
│ unique_booking_url           │
├──────────────────────────────┤
│ CUSTOM DOMAIN FIELDS:        │
├──────────────────────────────┤
│ custom_domain (CharField)    │◄─ okmentor.in
│ custom_domain_type (Char)    │◄─ "domain"
│ domain_verified (Boolean)    │◄─ True/False
│ domain_verification_code     │◄─ Random code
│ ssl_enabled (Boolean)        │◄─ True/False
│ cloudflare_hostname_id       │◄─ cf-id-12345
│ cname_target (CharField)     │◄─ customers.nextslot.in
│ txt_record_name (CharField)  │◄─ _bv-anju-mishra
├──────────────────────────────┤
│ PLAN FIELDS:                 │
├──────────────────────────────┤
│ current_plan (CharField)     │◄─ "pro"/"free"
│ plan_end_date (DateField)    │◄─ 2025-12-31
│ has_pro_features()           │◄─ Method
└──────────────────────────────┘
```

---

## DNS Configuration Examples

### Example 1: Custom Domain Setup (okmentor.in)

```
Domain Registrar (GoDaddy, Namecheap, etc.):

Type: A Record
Name: @ (or okmentor)
Value: (Cloudflare's IP - automatic)

OR

Type: CNAME Record
Name: @ (or okmentor)
Value: customers.nextslot.in

Optional (for verification):

Type: TXT Record
Name: _booking-verify
Value: {provider_verification_code}

Result:
okmentor.in → customers.nextslot.in → Railway App
```

### Example 2: Subdomain Setup (salon.nextslot.in)

```
Cloudflare Dashboard:

Existing Wildcard Record:
Type: CNAME
Name: *.nextslot.in
Value: web-production-200fb.up.railway.app
Proxied: Yes

No additional DNS setup needed!
salon.nextslot.in automatically works
```

---

## Middleware Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ Request arrives: okmentor.in/appointments/book/         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │ Skip Static/Media?    │
         │ /static/, /media/,    │
         │ /admin/               │
         └───────┬───────────────┘
                 │ NO
                 ▼
    ┌────────────────────────────┐
    │ Extract Host: okmentor.in  │
    └────────────┬───────────────┘
                 │
                 ▼
    ┌────────────────────────────────────┐
    │ Skip Default Domain?                │
    │ nextslot.in, www.nextslot.in,       │
    │ localhost, 127.0.0.1                │
    │ customers.nextslot.in               │
    │ *.railway.app                       │
    └────────┬──────────────────────────┘
             │ NO (okmentor.in is custom)
             ▼
    ┌────────────────────────────┐
    │ Subdomain Check            │
    │ ends with .nextslot.in?    │
    └────────┬───────────────────┘
             │ NO
             ▼
    ┌────────────────────────────────────┐
    │ External Custom Domain              │
    │ Query: ServiceProvider.get(         │
    │   custom_domain='okmentor.in',      │
    │   is_active=True                    │
    │ )                                   │
    └────────┬──────────────────────────┘
             │ FOUND
             ▼
    ┌────────────────────────────────────┐
    │ Set on Request:                     │
    │ request.custom_domain_provider      │
    │ request.is_custom_domain = True     │
    └────────┬──────────────────────────┘
             │
             ▼
    ┌────────────────────────────┐
    │ Root Path? (/ or ''?)      │
    └────────┬───────────────────┘
             │ YES
             ▼
    ┌────────────────────────────────────────────┐
    │ Redirect to:                               │
    │ /appointments/book/{provider.slug}/        │
    │ HTTP 302 Found                             │
    │ URL bar stays: okmentor.in                 │
    └────────────────────────────────────────────┘
```

---

## Cloudflare for SaaS Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  CLOUDFLARE FOR SAAS SETUP                      │
└─────────────────────────────────────────────────────────────────┘

                    Zone: nextslot.in
                    (Main Domain)
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐     ┌──────────┐     ┌──────────┐
    │ okmentor │     │ salon    │     │ fitness  │
    │   .in    │     │.nextslot │     │ .nextslot│
    │          │     │  .in     │     │   .in    │
    │ Custom   │     │Subdomain │     │Subdomain │
    │ Hostname │     │(Auto)    │     │(Auto)    │
    │ Status:  │     │Status:   │     │Status:   │
    │ ACTIVE   │     │ ACTIVE   │     │ ACTIVE   │
    │ SSL:     │     │SSL:      │     │SSL:      │
    │ ACTIVE   │     │ACTIVE    │     │ACTIVE    │
    │ CNAME:   │     │CNAME:    │     │CNAME:    │
    │ Manual   │     │Auto      │     │Auto      │
    │ Add      │     │(*.next   │     │(*.next   │
    │ CNAME    │     │ slot.in) │     │ slot.in) │
    └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │ Fallback Origin        │
              │ customers.nextslot.in  │
              │ (Railway App Domain)   │
              └────────┬───────────────┘
                       │
                       ▼
              ┌────────────────────────┐
              │ Railway App Server     │
              │ web-production-200fb   │
              │ .up.railway.app        │
              └────────────────────────┘
```

---

## Multi-Provider Example

```
Provider 1: Anju Mishra
├─ Business: Okmentor Services
├─ Custom Domain: okmentor.in
├─ Type: Custom Domain
├─ Verified: Pending
├─ Plan: PRO
└─ URL: https://okmentor.in/

Provider 2: Beauty Salon
├─ Business: Beauty & Spa
├─ Custom Domain: salon.nextslot.in
├─ Type: Subdomain
├─ Verified: Yes ✓
├─ Plan: PRO
└─ URL: https://salon.nextslot.in/

Provider 3: Fitness Center
├─ Business: FitLife Gym
├─ Custom Domain: fit.nextslot.in
├─ Type: Subdomain
├─ Verified: Yes ✓
├─ Plan: PRO
└─ URL: https://fit.nextslot.in/

Provider 4: John Doe
├─ Business: John's Consulting
├─ Custom Domain: (none)
├─ Type: None
├─ Verified: N/A
├─ Plan: FREE
└─ URL: https://nextslot.in/book/john-doe/

All domains route through same Rails App but show different content
based on the custom_domain_provider attached to the request.
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────┐
│           SECURITY LAYERS - REQUEST VALIDATION          │
└─────────────────────────────────────────────────────────┘

Layer 1: Cloudflare
├─ DDoS Protection
├─ WAF Rules
├─ SSL/TLS Encryption
└─ Rate Limiting

Layer 2: ALLOWED_HOSTS
├─ Django accepts * (any host)
├─ Validation done in middleware (not HTTP level)
└─ Prevents header injection attacks

Layer 3: CustomDomainMiddleware
├─ Validates host matches database entry
├─ Checks provider is_active status
├─ Only shows provider's own data
├─ Session/authentication still required

Layer 4: Provider Authentication
├─ Only authenticated provider can access booking page
├─ CSRF token protection
├─ XFrame options enabled
└─ Permission checks on views

Result: Each custom domain securely shows only that provider's data
```

---

## Performance Considerations

```
┌─────────────────────────────────────────────────────────┐
│          PERFORMANCE OPTIMIZATION STRATEGY              │
└─────────────────────────────────────────────────────────┘

Current (Per Request):
├─ 1 DB Query (find provider by domain)
├─ Middleware execution: ~5-10ms
├─ No caching layer
└─ Total overhead: ~10-15ms per request

Recommended Optimizations:

1. Middleware-level Caching
   ├─ Cache domain → provider_id mapping
   ├─ TTL: 1 hour
   ├─ Invalidate on domain change
   └─ Impact: -90% middleware overhead

2. Redis Caching
   from django.views.decorators.cache import cache_page
   @cache_page(3600)
   def get_provider_by_domain(domain):
       return ServiceProvider.objects.get(custom_domain=domain)

3. Database Indexing
   class ServiceProvider(Model):
       custom_domain = CharField(db_index=True)
       unique_together = [['custom_domain', 'is_active']]

4. CDN Caching
   ├─ Cache static content at Cloudflare
   ├─ Only dynamic requests hit Django
   └─ Impact: -95% response time

Recommended: Implement Redis caching for domain lookups
```

---

## Deployment Checklist

```
┌─────────────────────────────────────────────────────────┐
│        PRODUCTION DEPLOYMENT CHECKLIST                  │
└─────────────────────────────────────────────────────────┘

Pre-Deployment:
  [ ] Database migrations applied
  [ ] Cloudflare credentials in .env
  [ ] ALLOWED_HOSTS = '*'
  [ ] CustomDomainMiddleware in MIDDLEWARE list
  [ ] Django settings.py has DEFAULT_DOMAIN, RAILWAY_DOMAIN

DNS Setup:
  [ ] Fallback origin configured in Cloudflare
  [ ] customers.nextslot.in CNAME points to Railway
  [ ] Wildcard DNS for subdomains (*.nextslot.in)
  [ ] SSL certificates active in Cloudflare

Testing:
  [ ] Run python test_cloudflare.py
  [ ] Run python fix_cloudflare.py
  [ ] Test subdomain access
  [ ] Test custom domain with test entry
  [ ] Verify SSL certificates load

Post-Deployment:
  [ ] Monitor error logs for domain routing issues
  [ ] Check Cloudflare for SSL renewal
  [ ] Test each new custom domain added
  [ ] Document provider DNS setup process
  [ ] Create support guide for providers
```

---

## Troubleshooting Decision Tree

```
                    Domain Not Working?
                           │
                ┌──────────┼──────────┐
                │          │          │
                ▼          ▼          ▼
           DNS Issue   App Issue   Provider Issue
                │          │          │
           ┌────┴──┐   ┌───┴───┐    ┌┴─────────────┐
           │       │   │       │    │              │
           ▼       ▼   ▼       ▼    ▼              ▼
         Check  Check Test  Check Verify       Check
         CNAME  TLS   Apps  Logs   PRO Plan     DB Entry
         ✓      ✓     ✓      ✓     ✓             ✓
         │      │     │      │     │             │
         └──────┴─────┴──────┴─────┴─────────────┘
                          │
                          ▼
                 Domain Should Work!
                 If not → Contact Support
```

