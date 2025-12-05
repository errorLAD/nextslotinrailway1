"""
DigitalOcean DNS Management for Multiple Custom Domains

This module manages DNS configuration for each provider's custom domain on DigitalOcean.
Each provider can have multiple independent custom domains with their own DNS records.

Key Features:
- Independent DNS records per provider domain
- Automatic SSL certificate provisioning via Let's Encrypt
- Multi-domain support (unlimited domains per PRO provider)
- DNS validation and verification
- TTL and record type management

DNS Architecture:
1. Provider owns custom domain (e.g., okmentor.in)
2. Provider creates CNAME in their registrar: okmentor.in CNAME -> okmentor.nextslot.in
3. Provider subdomain CNAME: okmentor.nextslot.in CNAME -> app.ondigitalocean.app
4. DigitalOcean app resolves to 203.0.113.42 (example IP)
5. Let's Encrypt verifies domain and generates certificate
6. SSL auto-renews 30 days before expiry

Example Setup for okmentor.in:
================================
Step 1: Provider adds in registrar
  okmentor.in     CNAME  ->  okmentor.nextslot.in
  
Step 2: Subdomain setup (done once)
  okmentor.nextslot.in  CNAME  ->  my-booking-app.ondigitalocean.app

Step 3: Automatic
  - DigitalOcean detects okmentor.nextslot.in pointing to it
  - Let's Encrypt verifies domain ownership
  - SSL certificate generated
  - Both okmentor.in and okmentor.nextslot.in get HTTPS

Step 4: DNS Propagation
  - Usually 5-30 minutes
  - Can take up to 48 hours
  - Check at: mxtoolbox.com/cname
"""

from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DigitalOceanDNSManager:
    """
    Manages DNS configuration for provider custom domains on DigitalOcean.
    """
    
    def __init__(self):
        self.default_domain = getattr(settings, 'DEFAULT_DOMAIN', 'nextslot.in')
        self.do_app_domain = getattr(settings, 'DIGITALOCEAN_APP_DOMAIN', 'app.ondigitalocean.app')
        self.ttl = 3600  # 1 hour
    
    def get_dns_setup_info(self, provider):
        """
        Get complete DNS setup information for a provider's custom domain.
        
        Args:
            provider: ServiceProvider instance with custom_domain set
            
        Returns:
            dict: DNS configuration for display/setup
        """
        if not provider.custom_domain:
            return None
        
        custom_domain = provider.custom_domain.lower().strip()
        subdomain_name = provider.unique_booking_url.lower()
        subdomain = f"{subdomain_name}.{self.default_domain}"
        
        return {
            # Provider's custom domain
            'custom_domain': custom_domain,
            'custom_domain_with_www': f'www.{custom_domain}',
            
            # Provider's subdomain on default domain
            'subdomain': subdomain,
            'subdomain_with_www': f'www.{subdomain}',
            
            # DigitalOcean app domain
            'do_app_domain': self.do_app_domain,
            
            # DNS records to add
            'dns_records': [
                {
                    'name': 'Primary Custom Domain',
                    'type': 'CNAME',
                    'hostname': custom_domain,
                    'value': subdomain,
                    'ttl': self.ttl,
                    'description': f'Add in your domain registrar ({custom_domain})',
                    'priority': 1,
                    'status': self._check_dns_status(custom_domain, subdomain)
                },
                {
                    'name': 'Provider Subdomain (DigitalOcean)',
                    'type': 'CNAME',
                    'hostname': subdomain,
                    'value': self.do_app_domain,
                    'ttl': self.ttl,
                    'description': f'Add in nextslot.in DNS (managed centrally)',
                    'priority': 2,
                    'status': self._check_dns_status(subdomain, self.do_app_domain),
                    'note': 'Shared setup for all providers'
                },
                {
                    'name': 'TXT Verification Record',
                    'type': 'TXT',
                    'hostname': f'_booking-verify.{custom_domain}',
                    'value': provider.domain_verification_code or 'verification_code_pending',
                    'ttl': self.ttl,
                    'description': 'Optional: For additional domain verification',
                    'priority': 3,
                    'status': 'optional'
                }
            ],
            
            # A Record fallback (if CNAME not available)
            'a_record_fallback': {
                'type': 'A',
                'hostname': custom_domain,
                'value': '203.0.113.42',  # Placeholder IP - use your actual DigitalOcean app IP
                'ttl': self.ttl,
                'description': 'Use only if CNAME not available in your registrar',
                'priority': 99
            },
            
            # AAAA Record for IPv6 (if DigitalOcean supports)
            'aaaa_record': {
                'type': 'AAAA',
                'hostname': custom_domain,
                'value': '2001:db8::1',  # Placeholder IPv6 - use your actual DigitalOcean app IPv6
                'ttl': self.ttl,
                'description': 'Optional: IPv6 support (if enabled on DigitalOcean)',
                'priority': 98
            },
            
            # SSL Information
            'ssl_info': {
                'provider': 'Let\'s Encrypt',
                'type': 'Automatic',
                'domains': [custom_domain, subdomain],
                'renewal': 'Every 90 days (automatic)',
                'renewal_buffer': '30 days before expiry',
                'cost': 'Free',
                'encryption': '256-bit TLS',
                'http2': True,
                'hsts': 'Enabled'
            },
            
            # Timeline
            'setup_timeline': [
                {
                    'step': 1,
                    'title': 'Add DNS Record',
                    'time': '5 minutes',
                    'description': f'Add CNAME record in your registrar: {custom_domain} CNAME {subdomain}',
                    'completed': provider.domain_verified
                },
                {
                    'step': 2,
                    'title': 'DNS Propagation',
                    'time': '5-48 hours',
                    'description': f'DNS propagates across internet. Check at mxtoolbox.com',
                    'completed': False
                },
                {
                    'step': 3,
                    'title': 'Verify Domain',
                    'time': '2 minutes',
                    'description': 'Click "Verify Domain" button after DNS propagates',
                    'completed': provider.domain_verified
                },
                {
                    'step': 4,
                    'title': 'SSL Certificate',
                    'time': 'Automatic',
                    'description': 'Let\'s Encrypt generates certificate (5-30 min after verification)',
                    'completed': provider.ssl_enabled
                },
                {
                    'step': 5,
                    'title': 'Live!',
                    'time': 'Ready to use',
                    'description': f'Your domain is live: https://{custom_domain}',
                    'completed': provider.ssl_enabled
                }
            ]
        }
    
    def _check_dns_status(self, hostname, expected_value):
        """
        Check DNS resolution status for a hostname.
        
        Args:
            hostname: Domain/hostname to check
            expected_value: Expected CNAME/A record value
            
        Returns:
            str: Status ('pending', 'propagating', 'active', 'error')
        """
        try:
            import socket
            import dns.resolver
            
            # Try to resolve using DNS
            try:
                answers = dns.resolver.resolve(hostname, 'CNAME')
                if answers:
                    actual_value = str(answers[0].target).rstrip('.')
                    if actual_value.lower() == expected_value.lower():
                        return 'active'
                    else:
                        return 'mismatch'
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return 'pending'
            except Exception as e:
                logger.warning(f'Error checking DNS for {hostname}: {e}')
                return 'checking'
                
        except ImportError:
            # If dnspython not available, return 'checking'
            logger.warning('dnspython not installed - cannot check DNS status')
            return 'checking'
    
    def get_provider_subdomain(self, provider):
        """
        Get the provider's subdomain on the default domain.
        
        Args:
            provider: ServiceProvider instance
            
        Returns:
            str: Subdomain (e.g., 'okmentor.nextslot.in')
        """
        return f"{provider.unique_booking_url}.{self.default_domain}"
    
    def get_provider_cname_target(self, provider):
        """
        Get CNAME target for provider's custom domain.
        
        Args:
            provider: ServiceProvider instance
            
        Returns:
            str: CNAME target (provider's subdomain)
        """
        return self.get_provider_subdomain(provider)
    
    def get_provider_url(self, provider):
        """
        Get the provider's booking URL (with appropriate domain).
        
        Args:
            provider: ServiceProvider instance
            
        Returns:
            str: Full URL with provider's custom domain or subdomain
        """
        if provider.custom_domain and provider.domain_verified and provider.ssl_enabled:
            # Use custom domain with SSL
            return f"https://{provider.custom_domain}"
        elif provider.custom_domain and provider.domain_verified:
            # Custom domain but SSL pending - use http (not recommended)
            return f"http://{provider.custom_domain}"
        else:
            # Use subdomain fallback
            subdomain = self.get_provider_subdomain(provider)
            return f"https://{subdomain}"
    
    def format_dns_for_display(self, dns_info):
        """
        Format DNS information for template display.
        
        Args:
            dns_info: Output from get_dns_setup_info()
            
        Returns:
            dict: Formatted for template
        """
        if not dns_info:
            return None
        
        return {
            'domain': dns_info['custom_domain'],
            'subdomain': dns_info['subdomain'],
            'records': dns_info['dns_records'],
            'ssl': dns_info['ssl_info'],
            'timeline': dns_info['setup_timeline'],
            'info_url': f'https://mxtoolbox.com/cname/{dns_info["custom_domain"]}',
            'help_url': 'https://docs.digitalocean.com/products/app-platform/how-to/use-custom-domains/'
        }


class MultiProviderDNSManager:
    """
    Manages DNS configuration for multiple providers on DigitalOcean.
    Allows each provider to have independent custom domains.
    """
    
    def __init__(self):
        self.do_manager = DigitalOceanDNSManager()
    
    def get_all_provider_subdomains(self, providers):
        """
        Get list of all provider subdomains to add to nextslot.in DNS.
        
        Args:
            providers: QuerySet of ServiceProvider instances
            
        Returns:
            list: List of subdomains
        """
        subdomains = []
        for provider in providers.filter(is_active=True):
            subdomain = self.do_manager.get_provider_subdomain(provider)
            subdomains.append({
                'name': provider.business_name,
                'subdomain': subdomain,
                'status': 'active' if provider.domain_verified else 'pending',
                'ssl': 'active' if provider.ssl_enabled else 'pending'
            })
        return subdomains
    
    def get_dns_setup_summary(self):
        """
        Get summary of DNS setup needed for nextslot.in.
        
        Returns:
            dict: Centralized DNS setup information
        """
        do_domain = self.do_manager.do_app_domain
        default_domain = self.do_manager.default_domain
        
        return {
            'title': 'Centralized DNS Setup for nextslot.in',
            'description': 'One-time setup at your domain registrar',
            'records': [
                {
                    'type': 'CNAME (Wildcard)',
                    'name': f'*.{default_domain}',
                    'value': do_domain,
                    'ttl': 3600,
                    'note': 'Handles all provider subdomains',
                    'example': f'okmentor.{default_domain} -> {do_domain}'
                },
                {
                    'type': 'A Record (Fallback)',
                    'name': default_domain,
                    'value': '203.0.113.42',  # Your DigitalOcean app IP
                    'ttl': 3600,
                    'note': 'Alternative if CNAME not available'
                }
            ]
        }


# Convenience functions
def get_provider_dns_setup(provider):
    """Shortcut to get DNS setup for a provider."""
    manager = DigitalOceanDNSManager()
    return manager.get_dns_setup_info(provider)


def get_provider_url(provider):
    """Shortcut to get provider's URL."""
    manager = DigitalOceanDNSManager()
    return manager.get_provider_url(provider)
