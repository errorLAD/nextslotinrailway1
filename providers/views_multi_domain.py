"""
Views for managing multiple custom domains per provider.

This module handles:
- Adding multiple custom domains per provider
- Managing DNS records for each domain
- Verifying domains
- Setting primary domains
- Viewing domain status and management
"""

import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from .models import ServiceProvider, CustomDomain
from .simple_dns import (
    get_multi_domain_setup_instructions,
    verify_multi_domain,
    get_provider_domains_summary,
    create_custom_domain_record,
    set_primary_domain,
    delete_custom_domain,
)

logger = logging.getLogger(__name__)


def check_provider_permission(request):
    """Check if user is a provider and return provider instance."""
    if not hasattr(request.user, 'is_provider') or not request.user.is_provider:
        raise PermissionDenied("You don't have permission to access this page.")
    
    provider = request.user.provider_profile
    
    if not provider.has_pro_features():
        raise PermissionDenied("Multiple custom domains are only available for PRO users.")
    
    return provider


@login_required
def multi_domains_dashboard(request):
    """
    Dashboard showing all domains for a provider.
    Lists active, pending, and failed domains with management options.
    """
    provider = check_provider_permission(request)
    
    # Get all domains and their status
    domains_summary = get_provider_domains_summary(provider)
    
    # Get all domains for detailed view
    all_domains = CustomDomain.objects.filter(
        service_provider=provider,
        is_active=True
    ).order_by('-is_primary', '-added_at')
    
    context = {
        'provider': provider,
        'domains_summary': domains_summary,
        'all_domains': all_domains,
        'page_title': 'Multiple Custom Domains',
        'total_domains': all_domains.count(),
    }
    
    return render(request, 'providers/multi_domains_dashboard.html', context)


@login_required
def add_domain(request):
    """
    Add a new custom domain for the provider.
    """
    provider = check_provider_permission(request)
    
    if request.method == 'POST':
        domain_name = request.POST.get('domain_name', '').strip()
        domain_type = request.POST.get('domain_type', 'custom')
        dns_record_type = request.POST.get('dns_record_type', 'cname')
        
        # Validate domain name
        if not domain_name:
            messages.error(request, 'Please enter a domain name.')
            return redirect('providers:add_domain')
        
        if len(domain_name) < 5:
            messages.error(request, 'Domain name must be at least 5 characters.')
            return redirect('providers:add_domain')
        
        # Create the domain record
        result = create_custom_domain_record(provider, domain_name, domain_type)
        
        if result['success']:
            messages.success(
                request,
                f'Domain {domain_name} added successfully! Follow the DNS setup instructions.'
            )
            return redirect('providers:domain_setup', domain_id=result['domain_id'])
        else:
            messages.error(request, result.get('error', 'Failed to add domain.'))
    
    context = {
        'provider': provider,
        'page_title': 'Add New Domain',
    }
    
    return render(request, 'providers/add_domain.html', context)


@login_required
def domain_setup(request, domain_id):
    """
    Show DNS setup instructions for a specific domain.
    """
    provider = check_provider_permission(request)
    
    # Get domain - ensure it belongs to this provider
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    # Get setup instructions
    instructions = get_multi_domain_setup_instructions(custom_domain)
    
    context = {
        'provider': provider,
        'domain': custom_domain,
        'instructions': instructions,
        'page_title': f'Setup Domain - {custom_domain.domain_name}',
        'cname_target': custom_domain.cname_target,
        'verification_code': custom_domain.verification_code,
    }
    
    return render(request, 'providers/domain_setup.html', context)


@login_required
def domain_verify(request, domain_id):
    """
    Verify that DNS is properly configured for a domain.
    """
    provider = check_provider_permission(request)
    
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    if request.method == 'POST':
        # Verify the domain
        verification = verify_multi_domain(custom_domain)
        
        if verification['verified']:
            # Update domain status
            custom_domain.mark_verified()
            messages.success(
                request,
                f'Domain {custom_domain.domain_name} verified successfully!'
            )
        else:
            messages.warning(
                request,
                f'Domain verification pending. DNS may still be propagating. Try again in a few minutes.'
            )
        
        return redirect('providers:domain_manage', domain_id=domain_id)
    
    # GET request - show verification page
    verification = verify_multi_domain(custom_domain)
    
    context = {
        'provider': provider,
        'domain': custom_domain,
        'verification': verification,
        'page_title': f'Verify Domain - {custom_domain.domain_name}',
    }
    
    return render(request, 'providers/domain_verify.html', context)


@login_required
def domain_manage(request, domain_id):
    """
    Manage a specific domain - view status, SSL info, DNS records.
    """
    provider = check_provider_permission(request)
    
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    # Get detailed info
    verification = verify_multi_domain(custom_domain)
    instructions = get_multi_domain_setup_instructions(custom_domain)
    
    context = {
        'provider': provider,
        'domain': custom_domain,
        'verification': verification,
        'instructions': instructions,
        'page_title': f'Manage Domain - {custom_domain.domain_name}',
    }
    
    return render(request, 'providers/domain_manage.html', context)


@login_required
@require_POST
def set_primary(request, domain_id):
    """
    Set a domain as the primary/main domain for the provider.
    """
    provider = check_provider_permission(request)
    
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    if custom_domain.status != 'active':
        messages.error(
            request,
            'Domain must be fully active before setting as primary.'
        )
    else:
        if set_primary_domain(custom_domain):
            messages.success(
                request,
                f'{custom_domain.domain_name} is now your primary domain.'
            )
        else:
            messages.error(request, 'Failed to set primary domain.')
    
    return redirect('providers:multi_domains_dashboard')


@login_required
@require_POST
def remove_domain(request, domain_id):
    """
    Remove/delete a custom domain.
    """
    provider = check_provider_permission(request)
    
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    if custom_domain.is_primary:
        messages.error(
            request,
            'Cannot remove the primary domain. Set another domain as primary first.'
        )
    else:
        result = delete_custom_domain(custom_domain)
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result.get('error', 'Failed to remove domain.'))
    
    return redirect('providers:multi_domains_dashboard')


@login_required
def domain_status_json(request, domain_id):
    """
    API endpoint to get domain status as JSON.
    Useful for AJAX checks and real-time updates.
    """
    provider = check_provider_permission(request)
    
    custom_domain = get_object_or_404(
        CustomDomain,
        id=domain_id,
        service_provider=provider
    )
    
    verification = verify_multi_domain(custom_domain)
    
    return JsonResponse({
        'domain': custom_domain.domain_name,
        'domain_id': custom_domain.id,
        'status': custom_domain.status,
        'verified': verification['verified'],
        'ssl_enabled': verification['ssl_enabled'],
        'url': verification['access_url'],
        'added_at': custom_domain.added_at.isoformat(),
        'verified_at': verification['verified_at'].isoformat() if verification['verified_at'] else None,
        'ssl_expiry': verification['ssl_expiry'].isoformat() if verification['ssl_expiry'] else None,
    })


@login_required
def domains_list_json(request):
    """
    API endpoint to get all domains for a provider as JSON.
    """
    provider = check_provider_permission(request)
    
    domains = CustomDomain.objects.filter(
        service_provider=provider,
        is_active=True
    ).values(
        'id', 'domain_name', 'status', 'is_primary',
        'ssl_enabled', 'added_at', 'verified_at'
    ).order_by('-is_primary', '-added_at')
    
    return JsonResponse({
        'provider_id': provider.id,
        'total_domains': domains.count(),
        'domains': list(domains),
    })
