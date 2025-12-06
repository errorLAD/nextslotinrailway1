# DigitalOcean Spaces Environment Variables Setup

This guide shows you how to configure your `.env` file for DigitalOcean Spaces storage.

## 📋 Required Environment Variables

Add these to your `.env` file:

```env
# ============================================================================
# DigitalOcean Spaces Configuration
# ============================================================================

# DigitalOcean Spaces Access Credentials
# Get these from: DigitalOcean Dashboard > API > Spaces Keys
# Or: DigitalOcean Dashboard > Spaces > Your Space > Settings > Keys
DO_SPACES_ACCESS_KEY=your_digitalocean_spaces_access_key
DO_SPACES_SECRET_KEY=your_digitalocean_spaces_secret_key

# DigitalOcean Spaces Bucket Configuration
DO_SPACES_BUCKET_NAME=nextslootindia
DO_SPACES_REGION=sfo3
# Available regions: sfo3, nyc3, ams3, sgp1, fra1

# Optional: Custom Domain (if you have a CDN domain)
# DO_SPACES_CUSTOM_DOMAIN=cdn.yourdomain.com

# Optional: Custom Endpoint (auto-constructed if not provided)
# DO_SPACES_ENDPOINT_URL=https://sfo3.digitaloceanspaces.com
```

## 🔑 How to Get DigitalOcean Spaces Credentials

1. **Log in to DigitalOcean Dashboard**
   - Go to https://cloud.digitalocean.com/

2. **Navigate to API Section**
   - Click on "API" in the left sidebar
   - Or go to: https://cloud.digitalocean.com/account/api/spaces

3. **Generate Spaces Keys**
   - Click "Generate New Key"
   - Give it a name (e.g., "BookingSaaS Production")
   - Copy the **Access Key** and **Secret Key**
   - ⚠️ **Important:** The secret key is only shown once!

4. **Get Your Space Information**
   - Go to "Spaces" in the left sidebar
   - Select your Space (or create a new one)
   - Note the **Space name** (this is your bucket name)
   - Note the **Region** (e.g., sfo3, nyc3)

## 📝 Complete .env File Example

Here's a complete `.env` file with all DigitalOcean Spaces variables:

```env
# ============================================================================
# Django Settings
# ============================================================================
SECRET_KEY=django-insecure-dev-key-change-in-production-12345
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.ondigitalocean.app

# ============================================================================
# Database Configuration
# ============================================================================
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# ============================================================================
# DigitalOcean Spaces Configuration (Media File Storage)
# ============================================================================
DO_SPACES_ACCESS_KEY=your_digitalocean_spaces_access_key
DO_SPACES_SECRET_KEY=your_digitalocean_spaces_secret_key
DO_SPACES_BUCKET_NAME=nextslootindia
DO_SPACES_REGION=sfo3

# ============================================================================
# Email Configuration
# ============================================================================
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# ============================================================================
# Payment Gateway (Razorpay)
# ============================================================================
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxx

# ============================================================================
# Celery & Redis
# ============================================================================
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# ============================================================================
# Site Configuration
# ============================================================================
SITE_NAME=BookingSaaS
SITE_URL=http://localhost:8000
```

## 🔄 Migration from AWS S3 Variables

If you were using AWS S3 variables, replace them:

**Old (AWS S3):**
```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=your_bucket
AWS_S3_REGION_NAME=us-east-1
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com
```

**New (DigitalOcean Spaces):**
```env
DO_SPACES_ACCESS_KEY=your_key
DO_SPACES_SECRET_KEY=your_secret
DO_SPACES_BUCKET_NAME=your_bucket
DO_SPACES_REGION=sfo3
```

## ✅ Verification

After setting up your `.env` file:

1. **Restart your Django server**
   ```bash
   python manage.py runserver
   ```

2. **Test file upload**
   - Go to `/provider/profile/edit/`
   - Upload an image
   - Check if it appears correctly

3. **Verify in DigitalOcean**
   - Go to your Space in DigitalOcean Dashboard
   - Check if the uploaded file appears there

## 🚨 Troubleshooting

### Error: "Access Denied"
- **Solution:** Check that your `DO_SPACES_ACCESS_KEY` and `DO_SPACES_SECRET_KEY` are correct
- Verify the keys have proper permissions in DigitalOcean

### Error: "Bucket not found"
- **Solution:** Check that `DO_SPACES_BUCKET_NAME` matches your Space name exactly
- Verify the Space exists in the specified `DO_SPACES_REGION`

### Error: "Region mismatch"
- **Solution:** Ensure `DO_SPACES_REGION` matches your Space's region
- Available regions: `sfo3`, `nyc3`, `ams3`, `sgp1`, `fra1`

### Files not uploading
- **Solution:** Check that your Space has "File Listing" enabled
- Verify CORS settings if accessing from a web browser
- Check Django logs for detailed error messages

## 📚 Additional Resources

- [DigitalOcean Spaces Documentation](https://docs.digitalocean.com/products/spaces/)
- [DigitalOcean Spaces API Reference](https://docs.digitalocean.com/reference/api/spaces-api/)
- [Setting up CORS for Spaces](https://docs.digitalocean.com/products/spaces/how-to/configure-cors/)

