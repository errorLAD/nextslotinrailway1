"""
Views for managing custom domains for service providers.

This module uses Cloudflare for SaaS to handle custom domain provisioning.
Each provider can add their own domain, and Cloudflare automatically
handles SSL and routing.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .models import ServiceProvider
from .domain_utils import (
    setup_custom_domain, 
    verify_domain_ownership, 
    generate_verification_code,
    generate_unique_cname_target,
    generate_unique_txt_record_name
)
from .simple_dns import (
    get_dns_setup_instructions,
    generate_ssl_certificate,
    verify_custom_domain,
    get_custom_domain_status
)

@login_required
def custom_domain_page(request):
    """
    Dedicated page for managing custom domain settings.
    Uses Cloudflare for SaaS for automatic SSL provisioning.
    Each provider gets unique TXT record verification.
    """
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to access this page.")
    
    provider = request.user.provider_profile
    is_pro = provider.has_pro_features()
    
    if not is_pro:
        messages.info(request, 'Custom domains are only available for PRO users. Upgrade to PRO to use this feature.')
    
    # Get the CNAME target for simple DNS
    from .simple_dns import APP_DOMAIN
    cname_target = APP_DOMAIN
    
    # Ensure provider has unique TXT record name and verification code
    txt_record_name = provider.txt_record_name
    verification_code = provider.domain_verification_code
    
    if provider.custom_domain:
        # Generate if missing
        if not txt_record_name:
            txt_record_name = generate_unique_txt_record_name(provider)
            provider.txt_record_name = txt_record_name
        
        if not verification_code:
            verification_code = f'booking-verify-{generate_verification_code(12)}'
            provider.domain_verification_code = verification_code
        
        # Save if any updates were made
        if not provider.txt_record_name or not provider.domain_verification_code:
            provider.save(update_fields=['txt_record_name', 'domain_verification_code'])
    
    # Get DNS setup instructions instead of Cloudflare status
    dns_info = None
    if provider.custom_domain:
        dns_info = get_dns_setup_instructions(provider, provider.custom_domain)
    
    context = {
        'provider': provider,
        'default_domain': cname_target,  # CNAME target for DNS
        'is_pro': is_pro,
        'cname_target': cname_target,
        'txt_record_name': txt_record_name or generate_unique_txt_record_name(provider),
        'verification_code': verification_code or provider.domain_verification_code,
        'dns_setup': dns_info,  # Simple DNS instructions instead of Cloudflare
    }
    
    return render(request, 'providers/custom_domain.html', context)

@login_required
def domain_settings(request):
    """
    View for managing domain settings.
    Only available for PRO users.
    """
    # Only service providers can access this page
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to access this page.")
    
    provider = request.user.provider_profile
    is_pro = provider.has_pro_features()
    
    # If not PRO, show the page but with limited functionality
    if not is_pro:
        messages.info(request, 'Custom domains are only available for PRO users. Upgrade to PRO to use this feature.')
    
    # Get or generate unique CNAME target and TXT record name
    cname_target = provider.cname_target or generate_unique_cname_target(provider)
    txt_record_name = provider.txt_record_name or generate_unique_txt_record_name(provider)
    
    # Get the Railway domain for CNAME target
    railway_domain = getattr(settings, 'RAILWAY_DOMAIN', 'web-production-200fb.up.railway.app')
    
    context = {
        'provider': provider,
        'default_domain': railway_domain,  # Use Railway domain for CNAME
        'is_pro': is_pro,
        'cname_target': cname_target,
        'txt_record_name': txt_record_name,
    }
    
    return render(request, 'providers/domain/settings.html', context)

@login_required
@require_http_methods(['POST'])
def add_custom_domain(request):
    """
    Handle adding a custom domain or subdomain.
    Only available for PRO users.
    """
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to perform this action.")
    
    provider = request.user.provider_profile
    
    # Check if user has PRO features
    if not provider.has_pro_features():
        messages.warning(request, 'Custom domains are only available on the PRO plan. Please upgrade to continue.')
        return redirect('subscriptions:upgrade_to_pro')
    
    # Support both 'domain' and 'custom_domain' parameter names
    domain = request.POST.get('domain', '').strip().lower()
    if not domain:
        domain = request.POST.get('custom_domain', '').strip().lower()
    
    domain_type = request.POST.get('domain_type', 'domain')
    
    # Validate domain type
    if domain_type not in ['subdomain', 'domain']:
        domain_type = 'domain'
    
    # Clean up domain - remove protocol if present
    domain = domain.replace('https://', '').replace('http://', '').strip('/')
    
    # For subdomains, validate and construct full domain
    if domain_type == 'subdomain':
        # Basic validation
        if not domain.replace('-', '').isalnum():
            messages.error(request, 'Subdomain can only contain letters, numbers, and hyphens.')
            return redirect('providers:dashboard')
        
        if len(domain) < 3 or len(domain) > 63:
            messages.error(request, 'Subdomain must be between 3 and 63 characters long.')
            return redirect('providers:dashboard')
        
        # Construct full domain
        domain = f"{domain}.{settings.DEFAULT_DOMAIN}"
        
        # Auto-verify subdomains since they use our wildcard SSL
        # Subdomains don't need DNS verification - they work instantly
    else:
        # For custom domains, validate the domain format
        if not is_valid_domain(domain):
            messages.error(request, 'Please enter a valid domain name (e.g., book.yourdomain.com).')
            return redirect('providers:dashboard')
    
    # Setup the domain
    success, message, verification_code = setup_custom_domain(provider, domain, domain_type)
    
    if success:
        # For subdomains, auto-verify immediately
        if domain_type == 'subdomain':
            provider.domain_verified = True
            provider.ssl_enabled = True
            provider.save(update_fields=['domain_verified', 'ssl_enabled'])
            messages.success(request, f'🎉 Your subdomain "{domain}" is now active! Visit it now.')
        else:
            # For full custom domains, use simple DNS records
            dns_setup = get_dns_setup_instructions(provider, domain)
            ssl_setup = generate_ssl_certificate(domain, provider.pk)
            
            # Save domain info
            provider.domain_verification_code = provider.domain_verification_code or f'booking-verify-{generate_verification_code(12)}'
            provider.save(update_fields=['domain_verification_code'])
            
            # Show DNS setup instructions
            messages.success(
                request, 
                f'✅ Domain "{domain}" is ready for setup!\n\n'
                f'Add this CNAME record to your DNS provider:\n'
                f'Record Type: CNAME\n'
                f'Record Name: @\n'
                f'Record Value: {dns_setup["record_value"]}\n\n'
                f'DNS Propagation: 5 minutes to 48 hours\n'
                f'SSL Certificate: Automatic once DNS is verified\n\n'
                f'Questions? Visit your Custom Domain settings page.'
            )
        return redirect('providers:custom_domain')
    else:
        messages.error(request, message)
        return redirect('providers:custom_domain')

def is_valid_domain(domain):
    """
    Basic domain validation.
    """
    if not domain or len(domain) > 255:
        return False
    
    # Check for at least one dot and no spaces
    if '.' not in domain or ' ' in domain:
        return False
    
    # Check each part of the domain
    parts = domain.split('.')
    for part in parts:
        if not part or len(part) > 63:
            return False
        if not all(c.isalnum() or c == '-' for c in part):
            return False
        if part.startswith('-') or part.endswith('-'):
            return False
    
    return True

@login_required
def domain_verification(request):
    """
    Show domain verification instructions and status.
    Each provider has unique CNAME target and TXT record.
    """
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to access this page.")
    
    provider = request.user.provider_profile
    
    if not provider.custom_domain:
        messages.warning(request, 'No custom domain configured.')
        return redirect('providers:domain_settings')
    
    # Get or generate unique CNAME target and TXT record name
    cname_target = provider.cname_target or generate_unique_cname_target(provider)
    txt_record_name = provider.txt_record_name or generate_unique_txt_record_name(provider)
    
    context = {
        'provider': provider,
        'default_domain': settings.DEFAULT_DOMAIN,
        'verification_code': provider.domain_verification_code,
        'cname_target': cname_target,
        'txt_record_name': txt_record_name,
    }
    
    return render(request, 'providers/domain/verification.html', context)

@login_required
def verify_domain(request):
    """
    Verify domain ownership by checking DNS records.
    """
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to perform this action.")
    
    provider = request.user.provider_profile
    
    if not provider.has_pro_features():
        messages.warning(request, 'Custom domains are only available on the PRO plan. Please upgrade to continue.')
        return redirect('subscriptions:upgrade_to_pro')
    
    if not provider.custom_domain or not provider.domain_verification_code:
        messages.error(request, 'No domain or verification code found.')
        return redirect('providers:dashboard')
    
    success, message = verify_domain_ownership(provider)
    if success:
        provider.domain_verified = True
        provider.ssl_enabled = True
        provider.save(update_fields=['domain_verified', 'ssl_enabled'])
        messages.success(request, 'Domain verified successfully! Your custom domain is now active with SSL.')
    else:
        provider.domain_verified = False
        provider.ssl_enabled = False
        provider.save(update_fields=['domain_verified', 'ssl_enabled'])
        messages.warning(request, message + ' Make sure DNS records are configured at your domain registrar and propagated (may take up to 48 hours).')
    return redirect('providers:custom_domain')

@login_required
@require_http_methods(['POST'])
def remove_domain(request):
    """
    Remove a custom domain from the provider's account.
    """
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to perform this action.")
    
    provider = request.user.provider_profile
    
    domain = provider.custom_domain
    
    # Clear the custom domain and verification status
    provider.custom_domain = None
    provider.custom_domain_type = 'none'  # Reset to default, not None
    provider.domain_verified = False
    provider.domain_verification_code = ''
    provider.ssl_enabled = False
    provider.save()
    
    messages.success(request, f'Domain "{domain}" has been removed successfully.')
    return redirect('providers:custom_domain')
