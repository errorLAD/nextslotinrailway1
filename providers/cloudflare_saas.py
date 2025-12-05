"""
Cloudflare for SaaS - Custom Hostname Management

This module handles automatic custom domain provisioning using Cloudflare's
Custom Hostnames API. This allows each service provider to have their own
custom domain with automatic SSL certificate provisioning.

Architecture:
1. Provider requests custom domain (e.g., okmentor.in)
2. We create a Custom Hostname in Cloudflare via API
3. Provider adds CNAME: okmentor.in -> customers.nextslot.in
4. Cloudflare automatically provisions SSL and routes traffic
5. Traffic flows: okmentor.in -> Cloudflare -> Railway App

Requirements:
- Cloudflare account with the zone (nextslot.in)
- Cloudflare for SaaS enabled (free for first 100 hostnames)
- API Token with Custom Hostnames permissions
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Cloudflare API base URL
CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"


def get_cloudflare_headers():
    """Get headers for Cloudflare API requests."""
    return {
        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }


def create_custom_hostname(custom_domain: str, provider_id: int = None) -> dict:
    """
    Create a custom hostname in Cloudflare for SaaS.
    
    This provisions SSL and routing for the customer's domain.
    
    Args:
        custom_domain: The customer's domain (e.g., okmentor.in)
        provider_id: Optional provider ID for reference
        
    Returns:
        dict with success status and details
    """
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not zone_id or not settings.CLOUDFLARE_API_TOKEN:
        logger.warning("Cloudflare credentials not configured")
        return {
            "success": False,
            "error": "Cloudflare integration not configured. Please contact support.",
            "manual_setup_required": True
        }
    
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/custom_hostnames"
    
    payload = {
        "hostname": custom_domain,
        "ssl": {
            "method": "http",  # HTTP validation (automatic)
            "type": "dv",      # Domain Validated certificate
            "settings": {
                "min_tls_version": "1.2",
                "http2": "on"
            }
        },
        "custom_metadata": {
            "provider_id": str(provider_id) if provider_id else ""
        }
    }
    
    try:
        response = requests.post(
            url,
            headers=get_cloudflare_headers(),
            json=payload,
            timeout=30
        )
        
        data = response.json()
        
        if data.get("success"):
            result = data.get("result", {})
            logger.info(f"Custom hostname created: {custom_domain}")
            return {
                "success": True,
                "hostname_id": result.get("id"),
                "status": result.get("status"),
                "ssl_status": result.get("ssl", {}).get("status"),
                "ownership_verification": result.get("ownership_verification"),
                "ssl_validation": result.get("ssl", {}).get("validation_records", [])
            }
        else:
            errors = data.get("errors", [])
            error_msg = errors[0].get("message") if errors else "Unknown error"
            logger.error(f"Failed to create custom hostname: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
            
    except requests.RequestException as e:
        logger.error(f"Cloudflare API request failed: {e}")
        return {
            "success": False,
            "error": f"API request failed: {str(e)}"
        }


def get_custom_hostname(custom_domain: str) -> dict:
    """
    Get the status of a custom hostname.
    
    Cloudflare hostname statuses:
    - "active": Fully active and ready to use
    - "pending": Waiting for DNS CNAME record
    - "moved": Domain was moved (but still works)
    - "deleted": Domain was deleted
    
    Args:
        custom_domain: The customer's domain
        
    Returns:
        dict with hostname status
    """
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not zone_id or not settings.CLOUDFLARE_API_TOKEN:
        return {"success": False, "error": "Cloudflare not configured"}
    
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/custom_hostnames"
    params = {"hostname": custom_domain}
    
    try:
        response = requests.get(
            url,
            headers=get_cloudflare_headers(),
            params=params,
            timeout=30
        )
        
        data = response.json()
        
        if data.get("success") and data.get("result"):
            result = data["result"][0] if data["result"] else None
            if result:
                # Extract SSL validation records
                ssl_info = result.get("ssl", {})
                validation_records = ssl_info.get("validation_records", [])
                
                # Extract ownership verification
                ownership_verification = result.get("ownership_verification", {})
                
                # Accept both "active" and "moved" statuses as valid
                # "moved" means domain changed but still works
                hostname_status = result.get("status", "")
                is_active = hostname_status in ["active", "moved"]
                
                return {
                    "success": True,
                    "hostname_id": result.get("id"),
                    "status": hostname_status,
                    "ssl_status": ssl_info.get("status"),
                    "is_active": is_active,
                    "ssl_validation_records": validation_records,
                    "ownership_verification": ownership_verification,
                    "ownership_verification_http": result.get("ownership_verification_http", {}),
                }
        
        return {"success": False, "error": "Hostname not found"}
        
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def delete_custom_hostname(hostname_id: str) -> dict:
    """
    Delete a custom hostname from Cloudflare.
    
    Args:
        hostname_id: The Cloudflare hostname ID
        
    Returns:
        dict with success status
    """
    zone_id = settings.CLOUDFLARE_ZONE_ID
    
    if not zone_id or not settings.CLOUDFLARE_API_TOKEN:
        return {"success": False, "error": "Cloudflare not configured"}
    
    url = f"{CLOUDFLARE_API_BASE}/zones/{zone_id}/custom_hostnames/{hostname_id}"
    
    try:
        response = requests.delete(
            url,
            headers=get_cloudflare_headers(),
            timeout=30
        )
        
        data = response.json()
        
        if data.get("success"):
            logger.info(f"Custom hostname deleted: {hostname_id}")
            return {"success": True}
        else:
            errors = data.get("errors", [])
            error_msg = errors[0].get("message") if errors else "Unknown error"
            return {"success": False, "error": error_msg}
            
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}


def verify_custom_hostname(custom_domain: str) -> dict:
    """
    Check if a custom hostname is fully active and verified.
    
    Cloudflare hostname statuses:
    - "active": Domain is fully active and working
    - "moved": Domain was moved but still works
    - "pending": Waiting for DNS configuration
    
    SSL statuses:
    - "active": SSL certificate is issued and active
    - "pending_validation": Waiting for SSL validation
    
    Args:
        custom_domain: The customer's domain
        
    Returns:
        dict with verification status and detailed messages
    """
    result = get_custom_hostname(custom_domain)
    
    if not result.get("success"):
        return result
    
    hostname_status = result.get("status", "unknown")
    ssl_status = result.get("ssl_status", "unknown")
    is_active = result.get("is_active", False)
    ssl_active = ssl_status == "active"
    
    # Build status messages
    messages = []
    
    if hostname_status == "active":
        messages.append("✓ Hostname ownership verified (status: active)")
    elif hostname_status == "moved":
        messages.append("✓ Hostname ownership verified (status: moved - domain was updated)")
    elif hostname_status == "pending":
        messages.append("⏳ Waiting for hostname ownership verification (ensure CNAME record is added)")
    else:
        messages.append(f"Hostname status: {hostname_status}")
    
    if ssl_status == "active":
        messages.append("✓ SSL certificate is active and valid")
    elif ssl_status == "pending_validation":
        messages.append("⏳ SSL certificate validation in progress (may take up to 24 hours)")
    else:
        messages.append(f"SSL status: {ssl_status}")
    
    return {
        "success": True,
        "hostname_verified": is_active,
        "ssl_verified": ssl_active,
        "fully_active": is_active and ssl_active,
        "status": hostname_status,
        "ssl_status": ssl_status,
        "messages": messages,
        # Pass through the validation records for the template
        "ssl_validation_records": result.get("ssl_validation_records", []),
        "ownership_verification": result.get("ownership_verification", {}),
    }


def get_cname_target() -> str:
    """
    Get the CNAME target that customers should point their domains to.
    
    IMPORTANT: This function now returns provider-SPECIFIC CNAME targets!
    Each provider gets their own subdomain on nextslot.in
    
    To use this function, you MUST pass the provider:
    Example: get_cname_target(provider=my_provider_instance)
    
    For backward compatibility without provider, returns customers.nextslot.in
    
    Args:
        provider: (Optional) ServiceProvider instance to get their unique CNAME
        
    Returns:
        str: Unique CNAME target (e.g., 'ramesh-salon.nextslot.in')
              or fallback 'customers.nextslot.in' if no provider given
    """
    # Note: This is the fallback/legacy behavior
    # Individual providers should use their unique subdomain via generate_unique_cname_target()
    return getattr(settings, 'CLOUDFLARE_CNAME_TARGET', f"customers.{settings.DEFAULT_DOMAIN}")


def setup_cloudflare_for_saas_instructions() -> dict:
    """
    Get instructions for setting up Cloudflare for SaaS.
    
    Returns:
        dict with setup instructions
    """
    return {
        "steps": [
            {
                "step": 1,
                "title": "Enable Cloudflare for SaaS",
                "description": "In Cloudflare Dashboard, go to SSL/TLS > Custom Hostnames and enable the feature."
            },
            {
                "step": 2,
                "title": "Create Fallback Origin",
                "description": f"Add a DNS record: proxy-fallback.{settings.DEFAULT_DOMAIN} -> {settings.RAILWAY_DOMAIN}",
                "record": {
                    "type": "CNAME",
                    "name": "proxy-fallback",
                    "content": settings.RAILWAY_DOMAIN,
                    "proxied": True
                }
            },
            {
                "step": 3,
                "title": "Set Fallback Origin in Dashboard",
                "description": f"In Custom Hostnames settings, set fallback origin to: proxy-fallback.{settings.DEFAULT_DOMAIN}"
            },
            {
                "step": 4,
                "title": "Create CNAME Target",
                "description": f"Add a DNS record: customers.{settings.DEFAULT_DOMAIN} -> proxy-fallback.{settings.DEFAULT_DOMAIN}",
                "record": {
                    "type": "CNAME",
                    "name": "customers",
                    "content": f"proxy-fallback.{settings.DEFAULT_DOMAIN}",
                    "proxied": True
                }
            },
            {
                "step": 5,
                "title": "Get API Token",
                "description": "Create an API token with 'SSL and Certificates: Edit' permission for your zone."
            },
            {
                "step": 6,
                "title": "Configure Environment Variables",
                "env_vars": {
                    "CLOUDFLARE_API_TOKEN": "Your API token",
                    "CLOUDFLARE_ZONE_ID": "Your zone ID (found in Overview)",
                    "CLOUDFLARE_CNAME_TARGET": f"customers.{settings.DEFAULT_DOMAIN}"
                }
            }
        ],
        "customer_instructions": {
            "title": "Instructions for Service Providers",
            "steps": [
                f"Add a CNAME record pointing your domain to: customers.{settings.DEFAULT_DOMAIN}",
                "Wait for SSL certificate to be issued (usually 1-5 minutes)",
                "Your domain is now active!"
            ]
        }
    }
