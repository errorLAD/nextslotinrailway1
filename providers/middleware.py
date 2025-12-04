"""
Middleware for subscription plan checking and trial management.
"""
import uuid
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.http import Http404
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
    Middleware to handle custom domain routing for service providers.
    
    This middleware checks if the request is coming from a custom domain or subdomain
    and sets the appropriate provider in the request object.
    All providers use the same CNAME target (the main platform domain).
    
    DNS Configuration for Custom Domains:
    - CNAME: customer-domain.com -> nextslot.in (proxied via Cloudflare)
    - TXT: _bv-{slug}.customer-domain.com -> booking-verify-{code}
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for static/media files and admin
        if request.path.startswith(('/static/', '/media/', '/admin/')):
            return self.get_response(request)
        
        # Initialize default values
        request.custom_domain_provider = None
        request.is_custom_domain = False
            
        host = request.get_host().split(':')[0].lower()
        
        # Skip if it's the default domain or localhost
        default_domain = getattr(settings, 'DEFAULT_DOMAIN', 'nextslot.in')
        if host in [default_domain, 'localhost', '127.0.0.1'] or host.endswith('.railway.app'):
            return self.get_response(request)
        
        # Check if this is a subdomain of the default domain
        if host.endswith(f'.{default_domain}'):
            subdomain = host.replace(f'.{default_domain}', '')
            try:
                provider = ServiceProvider.objects.get(
                    custom_domain=host,
                    custom_domain_type='subdomain',
                    domain_verified=True,
                    is_active=True
                )
                request.custom_domain_provider = provider
                request.is_custom_domain = True
            except ServiceProvider.DoesNotExist:
                pass
        else:
            # This is an external custom domain (e.g., okmentor.in)
            try:
                provider = ServiceProvider.objects.get(
                    custom_domain=host,
                    domain_verified=True,
                    is_active=True
                )
                request.custom_domain_provider = provider
                request.is_custom_domain = True
                
            except ServiceProvider.DoesNotExist:
                # Also check with www prefix
                if host.startswith('www.'):
                    try:
                        provider = ServiceProvider.objects.get(
                            custom_domain=host[4:],  # Remove www.
                            domain_verified=True,
                            is_active=True
                        )
                        request.custom_domain_provider = provider
                        request.is_custom_domain = True
                    except ServiceProvider.DoesNotExist:
                        pass
                else:
                    # Try with www prefix
                    try:
                        provider = ServiceProvider.objects.get(
                            custom_domain=f'www.{host}',
                            domain_verified=True,
                            is_active=True
                        )
                        request.custom_domain_provider = provider
                        request.is_custom_domain = True
                    except ServiceProvider.DoesNotExist:
                        pass
        
        response = self.get_response(request)
        return response
