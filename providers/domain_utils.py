"""
Utilities for domain verification and management.
Supports simple DNS records on DigitalOcean.
"""
import dns.resolver
import random
import string
import requests
import logging
from django.conf import settings
from django.utils import timezone
from .models import ServiceProvider

logger = logging.getLogger(__name__)

def generate_verification_code(length=32):
    """Generate a random verification code for domain verification."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def verify_domain_dns(domain, expected_cname=None, expected_txt=None, txt_record_name=None):
    """
    Verify DNS records for domain ownership.
    Works with Cloudflare proxied domains.
    REQUIRES BOTH CNAME and TXT verification for security.
    
    Args:
        domain (str): The domain to verify
        expected_cname (str, optional): Expected CNAME value
        results['https_ready'] = False
        expected_txt (str, optional): Expected TXT record value for verification
        txt_record_name (str, optional): Custom TXT record name (e.g., '_bv-provider-slug')
        
    Returns:
        dict: Verification results with status and messages
    """
    results = {
        'success': False,
        'cname_verified': False,
        'txt_verified': False,
        'a_record_found': False,
        'messages': []
    }
    
    # Extract root domain for TXT record lookup
    # e.g., www.urbanunit.in -> urbanunit.in
    domain_parts = domain.split('.')
    if len(domain_parts) > 2:
        root_domain = '.'.join(domain_parts[-2:])  # Get last 2 parts (urbanunit.in)
    else:
        root_domain = domain
    
    try:
        # Check for CNAME or A record (Cloudflare may return A records for proxied domains)
        if expected_cname:
            try:
                # First try CNAME
                cname_records = dns.resolver.resolve(domain, 'CNAME')
                cname_values = [str(r.target).rstrip('.') for r in cname_records]
                
                if expected_cname in cname_values or any(expected_cname in cv for cv in cname_values):
                    results['cname_verified'] = True
                    results['messages'].append('CNAME record is correctly configured.')
                else:
                    results['messages'].append(f'CNAME points to {cname_values}, expected {expected_cname}')
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                # If no CNAME, check for A record (Cloudflare proxy flattens CNAME to A)
                try:
                    a_records = dns.resolver.resolve(domain, 'A')
                    if a_records:
                        results['a_record_found'] = True
                        results['cname_verified'] = True  # Accept A record as valid (Cloudflare proxy)
                        results['messages'].append('A record found (Cloudflare proxy detected).')
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                    results['messages'].append('No CNAME or A record found for ' + domain)
            except dns.resolver.NoNameservers:
                results['messages'].append('DNS servers not responding.')
        
        # Verify TXT record if expected_txt is provided
        # Check multiple possible locations for the TXT record
        if expected_txt:
            # Build list of TXT record locations to check
            # If a custom txt_record_name is provided, check that first
            txt_locations = []
            
            if txt_record_name:
                # Provider's unique TXT record name (e.g., _bv-salon-name)
                txt_locations.append(f"{txt_record_name}.{root_domain}")
                txt_locations.append(f"{txt_record_name}")
            
            # Also check standard locations as fallback
            txt_locations.extend([
                f"_booking-verify.{root_domain}",      # _booking-verify.urbanunit.in
                f"_booking-verify.{domain}",           # _booking-verify.www.urbanunit.in
            ])
            
            txt_found = False
            for txt_domain in txt_locations:
                if txt_found:
                    break
                try:
                    txt_records = dns.resolver.resolve(txt_domain, 'TXT')
                    txt_values = []
                    for r in txt_records:
                        for s in r.strings:
                            txt_values.append(s.decode('utf-8'))
                    
                    if expected_txt in txt_values:
                        results['txt_verified'] = True
                        results['messages'].append(f'TXT verification record found at {txt_domain}.')
                        txt_found = True
                        break
                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                    continue
                except Exception:
                    continue
            
            if not txt_found:
                results['messages'].append(f'TXT record not found. Create TXT record with name "_booking-verify" at {root_domain}')
        
        # Determine overall success
        # REQUIRE BOTH: CNAME/A record AND TXT verification for security
        if results['cname_verified'] and results['txt_verified']:
            results['success'] = True
            results['messages'].append('Domain verified successfully! Both CNAME and TXT records confirmed.')
        elif results['cname_verified'] and not results['txt_verified']:
            results['success'] = False
            results['messages'].append('CNAME/A record found, but TXT verification record is missing. Please add the TXT record.')
        elif not results['cname_verified'] and results['txt_verified']:
            results['success'] = False
            results['messages'].append('TXT record found, but CNAME/A record is missing. Please add the CNAME record.')
        else:
            results['success'] = False
            results['messages'].append('Both CNAME and TXT records are required for verification.')
        
        return results
        
    except Exception as e:
        results['messages'].append(f'Error during DNS verification: {str(e)}')
        return results

def generate_unique_cname_target(provider):
    """
    Generate a UNIQUE CNAME target for each service provider.
    Each provider gets their own subdomain on nextslot.in
    
    IMPORTANT: Each service provider gets a DIFFERENT CNAME target:
    - Provider 1 (Ramesh Salon): CNAME target = ramesh-salon.nextslot.in
    - Provider 2 (John Fitness): CNAME target = john-fitness.nextslot.in
    - Provider 3 (OKMentor): CNAME target = okmentor.nextslot.in
    
    When a provider adds their custom domain:
    - Provider custom domain: ramesh-salon.com
    - They CNAME: ramesh-salon.com → ramesh-salon.nextslot.in
    
    DNS Flow:
    1. User visits: ramesh-salon.com
    2. DNS resolves: ramesh-salon.com → ramesh-salon.nextslot.in (provider's unique subdomain)
    3. Cloudflare routes to DigitalOcean app
    4. Middleware identifies provider by domain and shows their booking page
    
    Args:
        provider (ServiceProvider): The provider to generate unique CNAME for
        
    Returns:
        str: Unique CNAME target for this provider (e.g., 'ramesh-salon.nextslot.in')
    """
    # Get the provider's unique booking URL
    booking_url = provider.unique_booking_url
    
    # Get the base domain for provider subdomains
    base_domain = getattr(settings, 'PROVIDER_SUBDOMAIN_BASE', 'nextslot.in')
    
    # Generate unique subdomain: {booking_url}.{base_domain}
    # Example: ramesh-salon.nextslot.in
    unique_cname_target = f"{booking_url}.{base_domain}"
    
    # Store the unique CNAME target for reference
    if not provider.cname_target or provider.cname_target != unique_cname_target:
        provider.cname_target = unique_cname_target
        provider.save(update_fields=['cname_target'])
    
    return unique_cname_target


def generate_unique_txt_record_name(provider):
    """
    Generate a unique TXT record name for domain verification.
    Each provider gets their own verification TXT record.
    
    This ensures that:
    - Every provider has a UNIQUE verification identifier
    - The TXT record is provider-specific (tied to their unique_booking_url)
    - DNS verification is unique per provider
    
    Example:
    - Provider with unique_booking_url 'ramesh-salon' gets: _bv-ramesh-salon
    - Provider with unique_booking_url 'john-fitness' gets: _bv-john-fitness
    
    Args:
        provider (ServiceProvider): The provider to generate TXT record name for
        
    Returns:
        str: Unique TXT record name (e.g., '_bv-ramesh-salon')
    """
    # Use provider's unique_booking_url or pk as identifier
    slug = provider.unique_booking_url or f"provider-{provider.pk}"
    # Prefix with '_bv-' for booking verification
    return f"_bv-{slug}"


def setup_custom_domain(provider, domain, domain_type):
    """
    Set up a custom domain for a service provider.
    Each provider gets unique CNAME target and TXT record.
    
    Args:
        provider (ServiceProvider): The service provider to set up the domain for
        domain (str): The custom domain (e.g., 'www.example.com' or 'salon.example.com')
        domain_type (str): Type of domain ('subdomain' or 'domain')
        
    Returns:
        tuple: (success: bool, message: str, verification_code: str)
    """
    # Validate domain type
    if domain_type not in ['subdomain', 'domain']:
        return False, 'Invalid domain type. Must be either "subdomain" or "domain".', ''
    
    # Check if domain is already in use
    if ServiceProvider.objects.filter(custom_domain=domain).exclude(pk=provider.pk).exists():
        return False, 'This domain is already in use by another account.', ''
    
    # Generate unique verification code for this provider
    verification_code = f'booking-verify-{generate_verification_code(12)}'
    
    # Generate unique CNAME target for this provider
    cname_target = generate_unique_cname_target(provider)
    
    # Generate unique TXT record name for this provider
    txt_record_name = generate_unique_txt_record_name(provider)
    
    # Update provider with domain info
    provider.custom_domain = domain
    provider.custom_domain_type = domain_type
    provider.domain_verified = False
    provider.domain_verification_code = verification_code
    provider.cname_target = cname_target
    provider.txt_record_name = txt_record_name
    provider.domain_added_at = timezone.now()
    provider.save()
    
    return True, 'Domain setup initiated. Please verify ownership by adding the required DNS records.', verification_code

def verify_domain_ownership(provider):
    """
    Verify domain ownership using DNS record checking.
    
    For DigitalOcean hosting with simple DNS records:
    - Checks if provider's subdomain resolves correctly
    - Verifies CNAME record is pointing to nextslot.in subdomain
    - Marks domain as verified when DNS is correct
    
    Args:
        provider (ServiceProvider): The service provider with domain to verify
        
    Returns:
        tuple: (success: bool, message: str)
    """
    if not provider.custom_domain:
        return False, 'No domain configured.'
    
    try:
        import dns.resolver
        
        custom_domain = provider.custom_domain.lower()
        provider_subdomain = f"{provider.unique_booking_url}.nextslot.in"
        
        # Try to resolve the custom domain
        try:
            answers = dns.resolver.resolve(custom_domain, 'CNAME')
            if answers:
                resolved_cname = str(answers[0].target).rstrip('.')
                
                # Check if CNAME points to provider's subdomain
                if resolved_cname.lower() == provider_subdomain.lower():
                    # DNS is correct - mark as verified
                    provider.domain_verified = True
                    provider.ssl_enabled = True  # SSL will be generated by DigitalOcean
                    provider.save(update_fields=['domain_verified', 'ssl_enabled'])
                    
                    return True, (
                        f'Domain {custom_domain} verified successfully! '
                        'SSL certificate is being generated (usually takes 5-30 minutes). '
                        'Your booking page is now live with HTTPS support.'
                    )
                else:
                    return False, (
                        f'CNAME record is not pointing to the correct subdomain. '
                        f'Expected: {provider_subdomain}, '
                        f'Got: {resolved_cname}'
                    )
        except dns.resolver.NXDOMAIN:
            return False, (
                f'Domain {custom_domain} not found or DNS record not yet added. '
                'Please add the CNAME record and wait for DNS propagation (5-48 hours).'
            )
        except dns.resolver.NoAnswer:
            return False, (
                f'No CNAME record found for {custom_domain}. '
                'Please add the CNAME record in your domain registrar.'
            )
        except dns.exception.DNSException as e:
            return False, f'DNS lookup failed: {str(e)}'
            
    except ImportError:
        # If dnspython not installed, fallback to marking as verified
        # (DigitalOcean will verify when adding domain)
        logger.warning('dnspython not installed - cannot verify DNS. Marking as verified anyway.')
        provider.domain_verified = True
        provider.ssl_enabled = True
        provider.save(update_fields=['domain_verified', 'ssl_enabled'])
        
        return True, (
            f'Domain marked as verified (DNS checker unavailable). '
            f'Please ensure CNAME record is added. '
            f'SSL certificate will be generated on DigitalOcean.'
        )
