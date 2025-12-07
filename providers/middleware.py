"""
Middleware for subscription plan checking and trial management.
"""
import uuid
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from .models import ServiceProvider


class SubscriptionCheckMiddleware:
    """
    Middleware to check subscription status on each request.
    Handles plan downgrades when PRO subscription expires.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check subscription status for authenticated providers
        if request.user.is_authenticated and hasattr(request.user, 'is_provider'):
            if request.user.is_provider and hasattr(request.user, 'provider_profile'):
                provider = request.user.provider_profile
                today = timezone.now().date()
                
                # Check if PRO subscription has expired
                if provider.current_plan == 'pro' and provider.plan_end_date:
                    if provider.plan_end_date < today:
                        provider.downgrade_to_free()
                        
                        # Show message only once per session
                        if not request.session.get('pro_expiry_shown'):
                            messages.warning(
                                request,
                                'Your PRO subscription has expired. You have been downgraded to the FREE plan.'
                            )
                            request.session['pro_expiry_shown'] = True
        
        response = self.get_response(request)
        return response


class CustomDomainMiddleware:
    """
    Enhanced middleware for custom domain handling with DigitalOcean App Platform.
    Supports both direct custom domains and subdomains of the main domain.
    
    How it works:
    1. For custom domains (e.g., example.com):
       - Provider adds CNAME: example.com -> your-app.ondigitalocean.app
       - We look up the provider by custom_domain field
       
    2. For subdomains (e.g., provider.nextslot.in):
       - We extract the subdomain and look up by unique_booking_url
       
    SSL is automatically handled by DigitalOcean's Let's Encrypt integration.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.default_domain = getattr(settings, 'DEFAULT_DOMAIN', 'nextslot.in')
        self.do_domain = getattr(settings, 'DIGITALOCEAN_APP_DOMAIN', 'app.ondigitalocean.app')
        
        # Domains that should skip custom domain processing
        self.skip_domains = {
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            self.default_domain,
            f'www.{self.default_domain}',
            self.do_domain,
            f'www.{self.do_domain}',
            'customers.' + self.default_domain
        }
    
    def __call__(self, request):
        # Skip for static/media files, admin, and health checks
        if any(request.path.startswith(p) for p in ('/static/', '/media/', '/admin/', '/.well-known/', '/health/')):
            return self.get_response(request)
            
        # Initialize request attributes
        request.custom_domain_provider = None
        request.is_custom_domain = False
        
        # Get the hostname and clean it
        host = self.get_clean_host(request)
        if not host:
            return self.get_response(request)
            
        # Skip processing for default domains
        if host in self.skip_domains or host.endswith(('.ondigitalocean.app', '.up.railway.app')):
            return self.get_response(request)
        
        # Find provider by custom domain or subdomain
        provider = self.find_provider_by_domain(host)
        if provider:
            request.custom_domain_provider = provider
            request.is_custom_domain = True
            
            # Redirect to HTTPS if not already secure
            if not request.is_secure() and not settings.DEBUG:
                return self.redirect_to_https(request)
            
            # Redirect root path to provider's booking page
            if request.path in ('/', ''):
                return redirect('appointments:public_booking', slug=provider.unique_booking_url)
        
        return self.get_response(request)
    
    def get_clean_host(self, request):
        """Extract and clean the hostname from the request."""
        host = request.get_host().split(':')[0].lower().strip()
        
        # Remove port if present
        if ':' in host:
            host = host.split(':', 1)[0]
            
        # Remove www. prefix for consistent matching
        if host.startswith('www.'):
            host = host[4:]
            
        return host
    
    def find_provider_by_domain(self, host):
        """Find a provider by custom domain or subdomain."""
        # First try exact match on custom_domain
        try:
            return ServiceProvider.objects.filter(
                custom_domain__iexact=host,
                is_active=True,
                domain_verified=True
            ).first()
        except ServiceProvider.DoesNotExist:
            pass
            
        # Then try subdomain match (e.g., provider.nextslot.in)
        if host.endswith(f'.{self.default_domain}'):
            subdomain = host.replace(f'.{self.default_domain}', '')
            if subdomain and subdomain != 'www':
                try:
                    return ServiceProvider.objects.get(
                        unique_booking_url__iexact=subdomain,
                        is_active=True
                    )
                except ServiceProvider.DoesNotExist:
                    pass
        return None
    
    def redirect_to_https(self, request):
        """Redirect to HTTPS version of the same URL."""
        url = request.build_absolute_uri(request.get_full_path())
        secure_url = url.replace('http://', 'https://', 1)
        return redirect(secure_url, permanent=True)
