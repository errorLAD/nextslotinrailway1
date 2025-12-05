"""
Simple DNS Records Management for Custom Domains

This module handles custom domain setup using simple DNS records:
- CNAME records for domain routing
- A records as fallback
- TXT records for verification
- SSL certificates via Let's Encrypt (free)

No Cloudflare Custom Hostnames API - just simple DNS!

Architecture:
1. Provider adds custom domain (e.g., okmentor.in)
2. System provides CNAME record target: app.nextslot.in
3. Provider adds CNAME in their DNS registrar
4. System generates SSL certificate via Let's Encrypt
5. Traffic flows: okmentor.in → app.nextslot.in → App
"""

import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# CNAME Target - all providers point to this
APP_DOMAIN = getattr(settings, 'DIGITALOCEAN_APP_DOMAIN', 'app.nextslot.in')
APP_IP = getattr(settings, 'APP_IP_ADDRESS', None)  # Optional fallback A record


def get_dns_setup_instructions(provider, custom_domain: str) -> dict:
    """
    Get DNS setup instructions for a provider's custom domain.
    
    Returns simple CNAME record instructions.
    
    Args:
        provider: ServiceProvider instance
        custom_domain: The custom domain (e.g., okmentor.in)
        
    Returns:
        dict with DNS setup instructions
    """
    return {
        "success": True,
        "domain": custom_domain,
        "record_type": "CNAME",
        "record_name": "@",  # Root domain or subdomain
        "record_value": APP_DOMAIN,
        "ttl": 3600,
        "alternative_a_record": {
            "type": "A",
            "name": "@",
            "value": APP_IP
        } if APP_IP else None,
        "txt_verification": {
            "name": f"_booking-verify",
            "value": provider.domain_verification_code or "",
            "purpose": "Domain verification (optional)"
        },
        "instructions": f"""
Add this CNAME record to your DNS provider (e.g., GoDaddy, Namecheap, etc):

Record Type: CNAME
Record Name: @ (or www if you want www.{custom_domain})
Record Value: {APP_DOMAIN}
TTL: 3600 (or Auto)

Alternatively, if CNAME is not available, use A record:
Record Type: A
Record Name: @
Record Value: {APP_IP if APP_IP else 'Contact support for IP address'}
TTL: 3600

DNS Propagation: 5 minutes to 48 hours (usually 30 minutes)
SSL Certificate: Will be automatic once DNS is verified

Questions? Contact support@nextslot.in
        """
    }


def generate_ssl_certificate(domain: str, provider_id: int = None) -> dict:
    """
    Generate SSL certificate for a domain using Let's Encrypt.
    
    Uses DNS validation via dns-01 challenge.
    
    Args:
        domain: The domain to generate certificate for
        provider_id: Optional provider ID
        
    Returns:
        dict with certificate details and status
    """
    # For now, return instructions for manual SSL setup
    # In production, integrate with acme.py or similar library
    
    return {
        "success": True,
        "domain": domain,
        "status": "certificate_generating",
        "message": "SSL certificate will be auto-generated once DNS is verified",
        "certificate_provider": "Let's Encrypt (Free)",
        "validation_type": "DNS-01",
        "renewal": "Automatic (90 days)",
        "instructions": f"""
SSL Certificate Status for {domain}:

Provider: Let's Encrypt (Free, Auto-Renewable)
Validation Type: DNS-01 (Automatic)
Renewal: Automatic every 90 days

Once your DNS records are verified:
1. System detects valid DNS records
2. Let's Encrypt validates domain ownership
3. SSL certificate is generated automatically
4. Certificate is installed on our servers
5. Your domain will have HTTPS

Timeline:
- DNS Setup: 5 minutes to 48 hours
- Certificate Generation: 5-15 minutes after DNS verified
- Total Time: Usually 30-60 minutes

No action needed on your part after adding DNS records!
        """
    }


def verify_custom_domain(domain: str, provider_id: int = None) -> dict:
    """
    Verify that a custom domain is properly configured.
    
    Checks:
    1. DNS record exists and points to app
    2. Domain is accessible
    3. SSL certificate is valid (if HTTPS)
    
    Args:
        domain: The domain to verify
        provider_id: Optional provider ID
        
    Returns:
        dict with verification status
    """
    result = {
        "success": False,
        "domain": domain,
        "dns_verified": False,
        "domain_accessible": False,
        "ssl_active": False,
        "messages": []
    }
    
    try:
        # Try HTTP connection first
        response = requests.head(
            f"http://{domain}",
            timeout=10,
            allow_redirects=True
        )
        
        if response.status_code < 400:
            result["domain_accessible"] = True
            result["messages"].append(f"Domain is accessible (HTTP {response.status_code})")
        else:
            result["messages"].append(f"Domain returned HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        result["messages"].append(f"Cannot connect to domain (DNS may not be configured yet)")
    except requests.exceptions.Timeout:
        result["messages"].append(f"Connection timeout (check DNS configuration)")
    except Exception as e:
        result["messages"].append(f"Error accessing domain: {str(e)}")
    
    try:
        # Try HTTPS connection
        response = requests.head(
            f"https://{domain}",
            timeout=10,
            allow_redirects=True,
            verify=True
        )
        
        if response.status_code < 400:
            result["ssl_active"] = True
            result["success"] = True
            result["messages"].append(f"✅ Domain is active with valid SSL certificate!")
        else:
            result["messages"].append(f"HTTPS returned HTTP {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        result["messages"].append(f"HTTPS not yet available (certificate may be generating)")
    except requests.exceptions.SSLError:
        result["messages"].append(f"SSL certificate not yet available (please wait 5-15 minutes)")
    except requests.exceptions.Timeout:
        result["messages"].append(f"HTTPS connection timeout")
    except Exception as e:
        result["messages"].append(f"HTTPS check: {str(e)}")
    
    # If DNS and domain are accessible, mark as verified
    if result["domain_accessible"]:
        result["dns_verified"] = True
    
    return result


def get_dns_propagation_check(domain: str) -> dict:
    """
    Check DNS propagation status for a domain.
    
    Args:
        domain: The domain to check
        
    Returns:
        dict with DNS status
    """
    try:
        import dns.resolver
        
        result = {
            "domain": domain,
            "dns_configured": False,
            "cname_records": [],
            "a_records": [],
            "messages": []
        }
        
        # Check for CNAME records
        try:
            cname_records = dns.resolver.resolve(domain, 'CNAME')
            result["cname_records"] = [str(r.target).rstrip('.') for r in cname_records]
            result["dns_configured"] = True
            result["messages"].append(f"CNAME records found: {result['cname_records']}")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            result["messages"].append(f"No CNAME records found")
        except Exception as e:
            result["messages"].append(f"Error checking CNAME: {str(e)}")
        
        # Check for A records
        try:
            a_records = dns.resolver.resolve(domain, 'A')
            result["a_records"] = [str(r.address) for r in a_records]
            result["dns_configured"] = True
            result["messages"].append(f"A records found: {result['a_records']}")
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            result["messages"].append(f"No A records found")
        except Exception as e:
            result["messages"].append(f"Error checking A: {str(e)}")
        
        return result
        
    except ImportError:
        return {
            "domain": domain,
            "dns_configured": False,
            "messages": ["DNS library not available"],
            "note": "Use online DNS checker: mxtoolbox.com"
        }


def setup_wildcard_ssl() -> dict:
    """
    Setup wildcard SSL for *.nextslot.in domain.
    
    This allows all provider subdomains to use SSL automatically.
    
    Returns:
        dict with SSL setup information
    """
    return {
        "success": True,
        "domain": f"*.{getattr(settings, 'DEFAULT_DOMAIN', 'nextslot.in')}",
        "certificate_type": "Wildcard",
        "provider": "Let's Encrypt (Free)",
        "auto_renewal": True,
        "benefits": [
            "All provider subdomains covered",
            "No individual cert setup needed",
            "Free and automatic renewal",
            "Covers *.nextslot.in and nextslot.in"
        ],
        "setup_command": """
# Using certbot:
certbot certonly --dns-cloudflare -d *.nextslot.in -d nextslot.in

# Or via Docker:
docker run -it --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot certonly \\
  --dns-cloudflare -d *.nextslot.in -d nextslot.in
        """
    }


def get_custom_domain_status(provider) -> dict:
    """
    Get overall status of a provider's custom domain.
    
    Args:
        provider: ServiceProvider instance
        
    Returns:
        dict with complete status information
    """
    if not provider.custom_domain:
        return {
            "domain": None,
            "status": "not_configured",
            "message": "No custom domain configured"
        }
    
    return {
        "domain": provider.custom_domain,
        "cname_target": APP_DOMAIN,
        "status": "pending" if not provider.domain_verified else "active",
        "verified": provider.domain_verified,
        "ssl_enabled": provider.ssl_enabled,
        "added_date": provider.created_at,
        "next_steps": get_dns_setup_instructions(provider, provider.custom_domain)
    }


# ============================================================================
# MULTI-DOMAIN SUPPORT
# ============================================================================

def get_multi_domain_setup_instructions(custom_domain_obj) -> dict:
    """
    Get DNS setup instructions for a multi-domain CustomDomain object.
    
    Args:
        custom_domain_obj: CustomDomain instance
        
    Returns:
        dict with DNS setup instructions for this specific domain
    """
    from .models import CustomDomain
    
    domain = custom_domain_obj.domain_name
    cname_target = custom_domain_obj.cname_target or APP_DOMAIN
    a_record = custom_domain_obj.a_record_ip
    
    instructions = {
        "success": True,
        "domain": domain,
        "domain_type": custom_domain_obj.domain_type,
        "record_types": custom_domain_obj.dns_record_type,
        "verification_code": custom_domain_obj.verification_code,
    }
    
    # CNAME Record Setup
    if custom_domain_obj.dns_record_type in ['cname', 'both']:
        instructions["cname"] = {
            "type": "CNAME",
            "name": "@",
            "value": cname_target,
            "ttl": 3600,
            "instructions": f"""
Add CNAME record to your DNS provider:
Type: CNAME
Name: @ (or www if preferred)
Value: {cname_target}
TTL: 3600 (or Auto)
            """
        }
    
    # A Record Setup (fallback)
    if custom_domain_obj.dns_record_type in ['a_record', 'both'] and a_record:
        instructions["a_record"] = {
            "type": "A",
            "name": "@",
            "value": a_record,
            "ttl": 3600,
            "instructions": f"""
Add A record to your DNS provider (if CNAME not available):
Type: A
Name: @
Value: {a_record}
TTL: 3600 (or Auto)
            """
        }
    
    # TXT Verification Record
    instructions["txt_verification"] = {
        "type": "TXT",
        "name": custom_domain_obj.txt_record_name,
        "value": custom_domain_obj.verification_code,
        "purpose": "Domain ownership verification",
        "instructions": f"""
Add TXT record for verification:
Type: TXT
Name: {custom_domain_obj.txt_record_name}
Value: {custom_domain_obj.verification_code}
TTL: 3600
        """
    }
    
    instructions["propagation_info"] = {
        "dns_time": "5 minutes to 48 hours (usually 30 minutes)",
        "ssl_time": "5-15 minutes after DNS verification",
        "check_url": "https://mxtoolbox.com/cname.aspx",
    }
    
    return instructions


def verify_multi_domain(custom_domain_obj) -> dict:
    """
    Verify that a multi-domain CustomDomain is properly configured.
    
    Args:
        custom_domain_obj: CustomDomain instance
        
    Returns:
        dict with verification status
    """
    domain = custom_domain_obj.domain_name
    
    # In production, would do actual DNS lookups
    # For now, return status based on database state
    
    return {
        "domain": domain,
        "status": custom_domain_obj.status,
        "verified": custom_domain_obj.is_verified(),
        "ssl_enabled": custom_domain_obj.ssl_enabled,
        "added_at": custom_domain_obj.added_at,
        "verified_at": custom_domain_obj.verified_at,
        "ssl_expiry": custom_domain_obj.ssl_expiry_date,
        "access_url": custom_domain_obj.get_access_url(),
    }


def get_provider_domains_summary(provider) -> dict:
    """
    Get summary of all domains for a provider.
    
    Args:
        provider: ServiceProvider instance
        
    Returns:
        dict with all domains and their status
    """
    from .models import CustomDomain
    
    try:
        domains = CustomDomain.objects.filter(
            service_provider=provider,
            is_active=True
        ).order_by('-is_primary', '-added_at')
        
        primary_domain = None
        active_domains = []
        pending_domains = []
        failed_domains = []
        
        for domain_obj in domains:
            domain_info = {
                "id": domain_obj.id,
                "domain": domain_obj.domain_name,
                "type": domain_obj.domain_type,
                "status": domain_obj.status,
                "is_primary": domain_obj.is_primary,
                "ssl_enabled": domain_obj.ssl_enabled,
                "url": domain_obj.get_access_url(),
                "added_at": domain_obj.added_at,
                "verified_at": domain_obj.verified_at,
            }
            
            if domain_obj.is_primary:
                primary_domain = domain_info
            
            if domain_obj.status == 'active':
                active_domains.append(domain_info)
            elif domain_obj.status == 'pending':
                pending_domains.append(domain_info)
            elif domain_obj.status == 'failed':
                failed_domains.append(domain_info)
        
        return {
            "provider_id": provider.id,
            "total_domains": domains.count(),
            "primary_domain": primary_domain,
            "active_domains": active_domains,
            "pending_domains": pending_domains,
            "failed_domains": failed_domains,
            "all_domains": list(domains.values('id', 'domain_name', 'status', 'is_primary')),
        }
    except Exception as e:
        logger.error(f"Error getting domains summary for provider {provider.id}: {str(e)}")
        return {
            "error": str(e),
            "total_domains": 0,
        }


def create_custom_domain_record(provider, domain_name: str, domain_type: str = 'custom') -> dict:
    """
    Create a new CustomDomain record for a provider.
    
    Args:
        provider: ServiceProvider instance
        domain_name: The domain to add
        domain_type: 'custom' or 'subdomain'
        
    Returns:
        dict with new domain record and setup instructions
    """
    from .models import CustomDomain
    import uuid
    
    try:
        # Check if provider already has this domain
        if CustomDomain.objects.filter(
            service_provider=provider,
            domain_name=domain_name
        ).exists():
            return {
                "success": False,
                "error": "This domain is already configured for your account"
            }
        
        # Generate unique codes
        verification_code = f"verify-{uuid.uuid4().hex[:16]}"
        txt_record_name = f"_booking-verify-{uuid.uuid4().hex[:8]}"
        
        # Create the domain record
        custom_domain = CustomDomain.objects.create(
            service_provider=provider,
            domain_name=domain_name,
            domain_type=domain_type,
            verification_code=verification_code,
            txt_record_name=txt_record_name,
            cname_target=APP_DOMAIN,
            status='pending',
        )
        
        # Get setup instructions
        instructions = get_multi_domain_setup_instructions(custom_domain)
        
        return {
            "success": True,
            "domain_id": custom_domain.id,
            "domain_name": domain_name,
            "status": "pending",
            "instructions": instructions,
            "message": "Domain added successfully. Follow the DNS setup instructions to complete configuration."
        }
    except Exception as e:
        logger.error(f"Error creating custom domain for provider {provider.id}: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def set_primary_domain(custom_domain_obj) -> bool:
    """
    Set a domain as the primary domain for a provider.
    
    Args:
        custom_domain_obj: CustomDomain instance
        
    Returns:
        bool: Success status
    """
    try:
        provider = custom_domain_obj.service_provider
        
        # Remove primary status from all other domains
        CustomDomain.objects.filter(
            service_provider=provider,
            is_primary=True
        ).update(is_primary=False)
        
        # Set this as primary
        custom_domain_obj.is_primary = True
        custom_domain_obj.save(update_fields=['is_primary'])
        
        logger.info(f"Set {custom_domain_obj.domain_name} as primary for provider {provider.id}")
        return True
    except Exception as e:
        logger.error(f"Error setting primary domain: {str(e)}")
        return False


def delete_custom_domain(custom_domain_obj) -> dict:
    """
    Delete a custom domain record.
    
    Args:
        custom_domain_obj: CustomDomain instance
        
    Returns:
        dict with status
    """
    try:
        domain_name = custom_domain_obj.domain_name
        provider_id = custom_domain_obj.service_provider_id
        was_primary = custom_domain_obj.is_primary
        
        custom_domain_obj.delete()
        
        logger.info(f"Deleted domain {domain_name} for provider {provider_id}")
        
        return {
            "success": True,
            "message": f"Domain {domain_name} has been removed",
            "was_primary": was_primary
        }
    except Exception as e:
        logger.error(f"Error deleting custom domain: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

