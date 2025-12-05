#!/usr/bin/env python
"""
Setup Let's Encrypt SSL Certificate for Wildcard Domain

This script helps setup a wildcard SSL certificate for *.nextslot.in

Requirements:
- certbot installed (apt install certbot)
- DNS credentials for Cloudflare or other DNS provider
"""

import subprocess
import os

def setup_lets_encrypt_ssl():
    """Setup Let's Encrypt wildcard SSL certificate."""
    
    print("\n" + "="*70)
    print("LETS ENCRYPT WILDCARD SSL SETUP")
    print("="*70)
    
    print("""
This script will setup a FREE SSL certificate for *.nextslot.in

What you need:
1. certbot installed
2. Cloudflare API credentials (for DNS validation)
3. Access to install certificates on your server

Steps:
1. Install certbot (if not installed)
2. Setup Cloudflare credentials
3. Generate wildcard certificate
4. Configure your app to use it
5. Setup auto-renewal
    """)
    
    # Check if certbot is installed
    print("\n1. Checking certbot installation...")
    result = subprocess.run(['certbot', '--version'], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {result.stdout.strip()}")
    else:
        print("❌ certbot not installed")
        print("\nInstall with:")
        print("  Ubuntu/Debian: sudo apt install certbot python3-certbot-dns-cloudflare")
        print("  CentOS/RHEL: sudo yum install certbot python3-certbot-dns-cloudflare")
        print("  Mac: brew install certbot")
        return False
    
    # Ask for domain
    print("\n2. Enter your domain:")
    domain = input("Domain (e.g., nextslot.in): ").strip()
    
    if not domain:
        domain = "nextslot.in"
    
    print(f"\nWill setup SSL for:")
    print(f"  - *.{domain}")
    print(f"  - {domain}")
    
    # Setup Cloudflare credentials
    print("\n3. Cloudflare credentials:")
    print("""
You need to create Cloudflare API credentials for DNS validation.

Steps:
1. Go to: https://dash.cloudflare.com/
2. Account Settings → API Tokens
3. Create Token with: Zone:Zone Read, Zone:DNS:Edit
4. Copy the API token
5. Create file: ~/.cloudflare.ini
    """)
    
    cloudflare_ini_path = os.path.expanduser("~/.cloudflare.ini")
    
    if os.path.exists(cloudflare_ini_path):
        print(f"✅ Found {cloudflare_ini_path}")
    else:
        print(f"⚠️  {cloudflare_ini_path} not found")
        print("\nCreate it with:")
        print("""
# ~/.cloudflare.ini
dns_cloudflare_api_token = YOUR_API_TOKEN_HERE
dns_cloudflare_dns_api_token = YOUR_API_TOKEN_HERE
        """)
        
        create_file = input("\nCreate this file now? (y/n): ").strip().lower()
        if create_file == 'y':
            api_token = input("Enter Cloudflare API token: ").strip()
            
            ini_content = f"""# Cloudflare API Credentials
dns_cloudflare_api_token = {api_token}
dns_cloudflare_dns_api_token = {api_token}
"""
            
            with open(cloudflare_ini_path, 'w') as f:
                f.write(ini_content)
            
            os.chmod(cloudflare_ini_path, 0o600)  # Restrict permissions
            print(f"✅ Created {cloudflare_ini_path}")
    
    # Generate certificate
    print(f"\n4. Generating SSL certificate for *.{domain}...")
    print("This may take 1-5 minutes...\n")
    
    cmd = [
        'certbot', 'certonly',
        '--dns-cloudflare',
        '--dns-cloudflare-credentials', cloudflare_ini_path,
        '-d', f'*.{domain}',
        '-d', domain,
        '--agree-tos',
        '-m', 'admin@nextslot.in',  # Change this
        '--non-interactive'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Certificate generated successfully!")
        print(f"\nCertificate location:")
        print(f"  Public: /etc/letsencrypt/live/{domain}/fullchain.pem")
        print(f"  Private: /etc/letsencrypt/live/{domain}/privkey.pem")
    else:
        print(f"❌ Certificate generation failed")
        print(f"Error: {result.stderr}")
        return False
    
    # Setup auto-renewal
    print("\n5. Setting up auto-renewal...")
    print("""
Certbot should auto-renew certificates every 90 days.

Check renewal timer:
  sudo systemctl status certbot-renew.timer

Test renewal (dry run):
  sudo certbot renew --dry-run
    """)
    
    # Verify renewal is enabled
    check_renewal = subprocess.run(
        ['sudo', 'systemctl', 'is-enabled', 'certbot-renew.timer'],
        capture_output=True,
        text=True
    )
    
    if check_renewal.returncode == 0:
        print("✅ Auto-renewal is enabled")
    else:
        print("⚠️  Auto-renewal may not be enabled")
        print("\nEnable it with:")
        print("  sudo systemctl enable certbot-renew.timer")
        print("  sudo systemctl start certbot-renew.timer")
    
    # Configure Django
    print("\n6. Configure Django to use the certificate:")
    print(f"""
In your Django settings (settings.py):

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

In your web server config (Nginx):

ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;

ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_prefer_server_ciphers on;
    """)
    
    print("\n" + "="*70)
    print("✅ SSL CERTIFICATE SETUP COMPLETE!")
    print("="*70)
    print("""
Next steps:
1. Configure your web server (Nginx/Apache) to use the certificate
2. Update Django settings
3. Restart your web server
4. Test: Visit https://yoursite.com (should show green lock)

Questions?
  - Let's Encrypt docs: https://letsencrypt.org/docs/
  - Certbot docs: https://certbot.eff.org/
  - Cloudflare DNS: https://dash.cloudflare.com/
    """)
    
    return True


if __name__ == "__main__":
    setup_lets_encrypt_ssl()
