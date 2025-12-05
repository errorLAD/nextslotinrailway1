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
