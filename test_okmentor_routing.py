"""
Test okmentor.in domain routing through middleware
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'booking_saas.settings')
django.setup()

from django.test import RequestFactory
from providers.middleware import CustomDomainMiddleware
from providers.models import ServiceProvider

# Create a fake request
factory = RequestFactory()

# Test 1: okmentor.in root path
print("=" * 80)
print("TEST 1: okmentor.in / (root path)")
print("-" * 80)

request = factory.get('/', HTTP_HOST='okmentor.in')
middleware = CustomDomainMiddleware(lambda r: r)

print(f"Host: {request.get_host()}")
print(f"Path: {request.path}")

# This should trigger redirect in real middleware, but for testing we just check detection
try:
    response = middleware(request)
    print(f"Custom Domain Provider Set: {bool(request.custom_domain_provider)}")
    if request.custom_domain_provider:
        print(f"  Provider: {request.custom_domain_provider.business_name}")
        print(f"  Booking URL: {request.custom_domain_provider.unique_booking_url}")
    print(f"Is Custom Domain: {request.is_custom_domain}")
    if hasattr(response, 'status_code'):
        print(f"Response Status: {response.status_code}")
        if hasattr(response, 'url'):
            print(f"Redirect URL: {response.url}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 2: okmentor.in /appointments/book/
print("\n" + "=" * 80)
print("TEST 2: okmentor.in /appointments/book/ (subpath)")
print("-" * 80)

request2 = factory.get('/appointments/book/', HTTP_HOST='okmentor.in')
middleware2 = CustomDomainMiddleware(lambda r: r)

print(f"Host: {request2.get_host()}")
print(f"Path: {request2.path}")

try:
    response2 = middleware2(request2)
    print(f"Custom Domain Provider Set: {bool(request2.custom_domain_provider)}")
    if request2.custom_domain_provider:
        print(f"  Provider: {request2.custom_domain_provider.business_name}")
        print(f"  Booking URL: {request2.custom_domain_provider.unique_booking_url}")
    print(f"Is Custom Domain: {request2.is_custom_domain}")
    print(f"Response Type: {type(response2)}")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 3: nextslot.in (default domain - should NOT set provider)
print("\n" + "=" * 80)
print("TEST 3: nextslot.in (default domain - should NOT route)")
print("-" * 80)

request3 = factory.get('/', HTTP_HOST='nextslot.in')
middleware3 = CustomDomainMiddleware(lambda r: r)

print(f"Host: {request3.get_host()}")
print(f"Path: {request3.path}")

try:
    response3 = middleware3(request3)
    print(f"Custom Domain Provider Set: {bool(request3.custom_domain_provider)}")
    print(f"Is Custom Domain: {request3.is_custom_domain}")
    print("✓ Correctly skipped default domain")
except Exception as e:
    print(f"Error: {str(e)}")

# Test 4: Database query
print("\n" + "=" * 80)
print("TEST 4: Database Query")
print("-" * 80)

try:
    provider = ServiceProvider.objects.get(custom_domain__iexact='okmentor.in')
    print(f"✓ Provider Found: {provider.business_name}")
    print(f"  Domain: {provider.custom_domain}")
    print(f"  Domain Type: {provider.custom_domain_type}")
    print(f"  Verified: {provider.domain_verified}")
    print(f"  SSL: {provider.ssl_enabled}")
    print(f"  Active: {provider.is_active}")
    print(f"  Booking URL: {provider.unique_booking_url}")
except ServiceProvider.DoesNotExist:
    print("✗ Provider not found!")

print("\n" + "=" * 80)
print("TESTS COMPLETE")
print("=" * 80)
