"""
Django settings for booking_saas project.
Multi-tenant appointment booking SaaS with freemium pricing.
testing image upaloda 
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production-12345')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,*.ondigitalocean.app').split(',')

# Domain configuration
DEFAULT_DOMAIN = config('DEFAULT_DOMAIN', default='nextslot.in')
DEFAULT_SCHEME = config('DEFAULT_SCHEME', default='https')

# ============================================================================
# HOSTING CONFIGURATION - DigitalOcean App Platform
# ============================================================================
# Each service provider gets their own unique subdomain and/or custom domain
# 
# Subdomain Examples (on nextslot.in):
#   - ramesh-salon.nextslot.in
#   - john-fitness.nextslot.in
#   - okmentor.nextslot.in
#
# Custom Domain Examples (provider's own domain):
#   - ramesh-salon.com
#   - john-fitness.com
#   - okmentor.in
#
# For each provider, they CNAME their custom domain to their subdomain
# Example: okmentor.in CNAME -> okmentor.nextslot.in
#          okmentor.nextslot.in CNAME -> your-app.ondigitalocean.app

# Base domain for provider subdomains
PROVIDER_SUBDOMAIN_BASE = config('PROVIDER_SUBDOMAIN_BASE', default=DEFAULT_DOMAIN)

# ============================================================================
# DigitalOcean App Platform Configuration (PRIMARY)
# ============================================================================
# Get your DigitalOcean App domain from: App Settings > Domains & HTTPS
# Example: my-booking-app-abc123.ondigitalocean.app
DIGITALOCEAN_APP_DOMAIN = config('DIGITALOCEAN_APP_DOMAIN', default='my-booking-app.ondigitalocean.app')

# Add DigitalOcean domain to ALLOWED_HOSTS if not already present
if DIGITALOCEAN_APP_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(DIGITALOCEAN_APP_DOMAIN)

# ============================================================================
# DEPRECATED: Cloudflare Settings (No Longer Used)
# ============================================================================
# These settings are kept for backward compatibility but are no longer used.
# We now use simple DNS records with DigitalOcean/Let's Encrypt instead.
CLOUDFLARE_API_TOKEN = config('CLOUDFLARE_API_TOKEN', default='')
CLOUDFLARE_ZONE_ID = config('CLOUDFLARE_ZONE_ID', default='')
CLOUDFLARE_ACCOUNT_ID = config('CLOUDFLARE_ACCOUNT_ID', default='')
CLOUDFLARE_CNAME_TARGET = config('CLOUDFLARE_CNAME_TARGET', default='customers.nextslot.in')

# Add the default domain to ALLOWED_HOSTS if not already present
if DEFAULT_DOMAIN not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(DEFAULT_DOMAIN)

# Allow all subdomains of the default domain (for provider subdomains)
ALLOWED_HOSTS.append(f'.{DEFAULT_DOMAIN}')

# ============================================================================
# CUSTOM DOMAIN SUPPORT - Multiple Providers with Independent Domains
# ============================================================================
# Each provider can have their own custom domain with independent SSL certificates
# DNS Setup:
#   1. Provider's domain CNAME -> provider-slug.nextslot.in
#   2. provider-slug.nextslot.in CNAME -> your-app.ondigitalocean.app
#   3. Let's Encrypt auto-generates SSL for both provider domain and subdomain
#
# Example for okmentor.in:
#   okmentor.in CNAME okmentor.nextslot.in
#   okmentor.nextslot.in CNAME my-booking-app.ondigitalocean.app
#   Both domains get Let's Encrypt SSL automatically

# Allow ANY custom domain - validated in middleware
ALLOWED_HOSTS.append('*')  # Accept all hosts - we validate in CustomDomainMiddleware

# ============================================================================
# SSL/HTTPS Configuration
# ============================================================================
# Let's Encrypt automatically provisions SSL for all domains when:
# 1. DNS records are properly configured
# 2. Domain resolves to your DigitalOcean app
# 3. HTTPS is enabled in DigitalOcean App Settings


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    # Third-party apps
    'django_celery_beat',
    'mathfilters',
    # Local apps
    'accounts.apps.AccountsConfig',
    'providers.apps.ProvidersConfig',
    'appointments.apps.AppointmentsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'utils.apps.UtilsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Custom middleware
    'providers.middleware.SubscriptionCheckMiddleware',
    'providers.middleware.CustomDomainMiddleware',
]

ROOT_URLCONF = 'booking_saas.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'booking_saas.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DB_ENGINE = config('DB_ENGINE', default='django.db.backends.sqlite3')

if 'postgresql' in DB_ENGINE:
    # PostgreSQL configuration (Railway)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='railway'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }
else:
    # SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / config('DB_NAME', default='db.sqlite3'),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'  # Indian Standard Time

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise static files storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Additional locations of static files
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'subscriptions/static',
]

# Media files (User uploads) - Stored in PostgreSQL
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Use local filesystem storage for uploaded files
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Ensure the media directory exists
os.makedirs(MEDIA_ROOT, exist_ok=True)

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'providers:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@nextslot.in')

# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# SSL Configuration for custom domains
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG  # Redirect all non-HTTPS requests to HTTPS in production

# ============================================================================
# Let's Encrypt SSL Configuration
# ============================================================================
# DigitalOcean App Platform automatically manages Let's Encrypt certificates for:
# 1. All domains listed in your DigitalOcean App Settings
# 2. All provider custom domains (once DNS is verified)
#
# How it works:
# 1. Provider adds CNAME record in their registrar
#    Example: okmentor.in CNAME okmentor.nextslot.in
# 2. okmentor.nextslot.in resolves to your DigitalOcean app
# 3. DigitalOcean/Let's Encrypt verifies domain ownership
# 4. SSL certificate is automatically generated (90-day expiry)
# 5. Certificate auto-renews 30 days before expiry
#
# To add a new provider domain to SSL:
# 1. Provider completes DNS setup (adds CNAME record)
# 2. Visit domain in browser (wait for DNS propagation ~5-48 hours)
# 3. DigitalOcean detects new domain and provisions SSL
# 4. No manual SSL setup needed!

# ACME Challenge for Let's Encrypt verification (DigitalOcean managed)
# No configuration needed - DigitalOcean handles ACME challenge automatically
ACME_WELL_KNOWN_URL = '/.well-known/acme-challenge/'

# Custom domain SSL status tracking
CUSTOM_DOMAIN_SSL_CHECK_INTERVAL = 3600  # Check SSL status every hour (seconds)
CUSTOM_DOMAIN_VERIFICATION_TIMEOUT = 86400  # 24 hours to verify domain before SSL

# Server email (for error notifications)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Custom domain settings
CUSTOM_DOMAIN_VERIFICATION_TIMEOUT = 86400  # 24 hours in seconds

# Logging configuration for domain verification
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'domain_verification.log',
        },
    },
    'loggers': {
        'providers.domain_utils': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Razorpay Configuration
RAZORPAY_KEY_ID = config('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = config('RAZORPAY_KEY_SECRET', default='')
RAZORPAY_WEBHOOK_SECRET = config('RAZORPAY_WEBHOOK_SECRET', default='')

# Site Configuration
SITE_NAME = config('SITE_NAME', default='BookingSaaS')
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Subscription Plans Configuration
FREE_PLAN_APPOINTMENT_LIMIT = 5
FREE_PLAN_SERVICE_LIMIT = 3
PRO_PLAN_PRICE = 199  # in INR
TRIAL_PERIOD_DAYS = 14
GRACE_PERIOD_DAYS = 3

# Session Configuration
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_SAVE_EVERY_REQUEST = False

# Twilio SMS Configuration (PRO Plan Only)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')

# Email Tracking
EMAIL_TRACK_DELIVERY = True

# Notification Settings
SEND_WELCOME_EMAIL = True
SEND_APPOINTMENT_CONFIRMATION = True
SEND_APPOINTMENT_REMINDER = True
REMINDER_HOURS_BEFORE = 24

# Google Calendar API (PRO plan only)
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')

# OpenAI API (AI Features)
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')

# CSRF Trusted Origins (Required for Railway)
CSRF_TRUSTED_ORIGINS = [
    'https://web-production-200fb.up.railway.app',
    'https://*.railway.app',
    'https://nextslot.in',
    'https://www.nextslot.in',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Allow all hosts in Railway (Railway handles this via proxy)
if os.environ.get('RAILWAY_ENVIRONMENT'):
    ALLOWED_HOSTS = ['*']
    DEBUG = False
