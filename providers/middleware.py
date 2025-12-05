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
    Middleware to handle custom domain routing for service providers.
    
    Supports multiple providers with independent custom domains on DigitalOcean.
    
    How it works:
    1. Provider adds CNAME record: custom-domain.com CNAME -> provider-slug.nextslot.in
    2. provider-slug.nextslot.in CNAME -> app.ondigitalocean.app (handled in DNS registrar)
    3. When request comes to custom-domain.com, middleware routes to provider's booking page
    4. Let's Encrypt automatically generates SSL certificates for all domains
    
    Example for okmentor.in:
    - User visits okmentor.in
    - Middleware finds provider with custom_domain='okmentor.in'
    - Redirects to /book/okmentor/ (provider's public booking page)
    - All served under okmentor.in with Let's Encrypt SSL
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for static/media files and admin
        if request.path.startswith(('/static/', '/media/', '/admin/', '/.well-known/')):
            return self.get_response(request)
        
        # Initialize default values
        request.custom_domain_provider = None
        request.is_custom_domain = False
            
        host = request.get_host().split(':')[0].lower().strip()
        
        # Remove www prefix for checking
        check_host = host[4:] if host.startswith('www.') else host
        
        # Skip if it's the default domain, DigitalOcean domain, or localhost
        default_domain = getattr(settings, 'DEFAULT_DOMAIN', 'nextslot.in')
        do_domain = getattr(settings, 'DIGITALOCEAN_APP_DOMAIN', 'app.ondigitalocean.app')
        
        skip_hosts = [
            default_domain, 
            f'www.{default_domain}', 
            'localhost', 
            '127.0.0.1', 
            'customers.' + default_domain,
            do_domain,
            f'www.{do_domain}'
        ]
        
        # Skip DigitalOcean App Platform domains
        if check_host in skip_hosts or host.endswith('.ondigitalocean.app') or host.endswith('.up.railway.app'):
            return self.get_response(request)
        
        # Check if this is a subdomain of the default domain (e.g., okmentor.nextslot.in)
        if check_host.endswith(f'.{default_domain}'):
            subdomain = check_host.replace(f'.{default_domain}', '')
            if subdomain and subdomain != 'www' and subdomain != 'customers':
                try:
                    # For subdomains, check by subdomain match
                    provider = ServiceProvider.objects.get(
                        custom_domain=check_host,
                        is_active=True
                    )
                    request.custom_domain_provider = provider
                    request.is_custom_domain = True
                    
                    # Redirect to provider's booking page if at root
                    if request.path == '/' or request.path == '':
                        return redirect('appointments:public_booking', slug=provider.unique_booking_url)
                        
                except ServiceProvider.DoesNotExist:
                    # Try to find by unique_booking_url matching subdomain
                    try:
                        provider = ServiceProvider.objects.get(
                            unique_booking_url=subdomain,
                            is_active=True
                        )
                        request.custom_domain_provider = provider
                        request.is_custom_domain = True
                        
                        if request.path == '/' or request.path == '':
                            return redirect('appointments:public_booking', slug=provider.unique_booking_url)
                    except ServiceProvider.DoesNotExist:
                        pass
        else:
            # This is an external custom domain (e.g., okmentor.in)
            # Each provider can have their own independent custom domain
            # Try to find provider by custom domain (check both with and without www)
            provider = None
            
            # Try exact match first (case-insensitive)
            try:
                provider = ServiceProvider.objects.get(
                    custom_domain__iexact=check_host,
                    is_active=True
                )
            except ServiceProvider.DoesNotExist:
                # Try with www prefix
                try:
                    provider = ServiceProvider.objects.get(
                        custom_domain__iexact=f'www.{check_host}',
                        is_active=True
                    )
                except ServiceProvider.DoesNotExist:
                    # Try without www if original had www
                    if host.startswith('www.'):
                        try:
                            provider = ServiceProvider.objects.get(
                                custom_domain__iexact=host,
                                is_active=True
                            )
                        except ServiceProvider.DoesNotExist:
                            pass
            
            if provider:
                request.custom_domain_provider = provider
                request.is_custom_domain = True
                
                # Redirect to provider's booking page if at root
                if request.path == '/' or request.path == '':
                    return redirect('appointments:public_booking', slug=provider.unique_booking_url)
        
        response = self.get_response(request)
        return response
