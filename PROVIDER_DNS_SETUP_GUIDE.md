# 🚀 Custom Domain Setup - Step by Step

## Your Domain is Ready!

We're so glad you want to use your own domain with NextSlot!

### What You'll Get
✅ Your custom domain working with our booking system  
✅ Free SSL certificate (green lock 🔒)  
✅ Professional appearance  
✅ Full control over your booking URL  

---

## The Simple 3-Step Process

### Step 1: Add a DNS Record (5 minutes)

Go to your **Domain Registrar** (where you bought your domain):
- GoDaddy
- Namecheap
- Google Domains
- Route53 (AWS)
- Or wherever you registered your domain

**Find: DNS Settings or DNS Management**

Add this record:

```
Record Type: CNAME
Record Name: @ (or www)
Record Value: app.nextslot.in
TTL: 3600 (or leave as default)
```

**Click: Save/Apply**

> **Note:** It might say "CNAME" and "Value" or "Points to" or "Target" depending on your registrar. It's the same thing.

### Step 2: Wait for DNS (5 minutes to 24 hours)

DNS propagation takes time. Here's what happens:

**Timeline:**
- ⏱️ 5-15 minutes: Usually works
- ⏱️ 30 minutes: Most cases
- ⏱️ 1-24 hours: Rare cases

**Check if it's working:**

1. Open this website: https://www.mxtoolbox.com/mxlookup/
2. Enter your domain: `okmentor.in`
3. Click "DNS Lookup"
4. Look for: `okmentor.in CNAME app.nextslot.in`

If you see it, DNS is working! ✅

### Step 3: Your Domain is Ready! (Automatic)

Once DNS is setup, two things happen automatically:

1. **SSL Certificate** - Within 5-15 minutes
   - Your domain gets a free SSL certificate
   - You'll see a green lock 🔒 in browsers
   - Takes care of automatically

2. **Booking Page** - Immediately
   - Your booking page loads on your domain
   - Customers can book appointments
   - Everything just works!

---

## Which Registrar Do You Use?

### GoDaddy

1. Go to: https://www.godaddy.com/
2. Sign in to your account
3. Click: "My Products"
4. Find your domain, click: "Manage"
5. Click: "DNS" (left menu)
6. Under "Records", click: "Add"
7. Select: "CNAME"
8. Enter:
   - **Name:** @ (or www)
   - **Value:** app.nextslot.in
   - **TTL:** 3600
9. Click: "Save"

### Namecheap

1. Go to: https://www.namecheap.com/
2. Sign in to your account
3. Go to: "Domain List"
4. Click: "Manage" (for your domain)
5. Click: "Advanced DNS" (top menu)
6. Click: "Add New Record"
7. Select: "CNAME Record"
8. Enter:
   - **Host:** @ (or www)
   - **Value:** app.nextslot.in
   - **TTL:** 3600
9. Click: "Save"

### Google Domains

1. Go to: https://domains.google.com/
2. Select your domain
3. Click: "DNS" (left menu)
4. Scroll down to: "Custom records"
5. Click: "Create new record"
6. Select: "CNAME"
7. Enter:
   - **Name:** @ (or www)
   - **Type:** CNAME
   - **Data:** app.nextslot.in
   - **TTL:** 3600
8. Click: "Create"

### Route53 (AWS)

1. Go to: https://console.aws.amazon.com/route53/
2. Click: "Hosted zones"
3. Find your domain
4. Click: "Create record"
5. Leave "Record name" empty (for @)
6. Select: "CNAME"
7. Enter: app.nextslot.in
8. Click: "Create records"

### Other Registrars

If you use a different registrar:
1. Look for "DNS Management" or "DNS Settings"
2. Add a new record
3. Select type: "CNAME"
4. Name: @ (or www)
5. Value: app.nextslot.in
6. Save

> **Still stuck?** Contact your registrar's support. They can add the CNAME record for you. Just tell them:
> - Type: CNAME
> - Name: @ (root domain)
> - Points to: app.nextslot.in

---

## Common Questions

### Q: What's a CNAME record?

A CNAME (Canonical Name) record tells the internet: "When someone visits okmentor.in, send them to app.nextslot.in instead."

It's like a forwarding address for your domain.

### Q: What's @ in Record Name?

@ means "root domain" (the main domain without www)

- `@` = okmentor.in
- `www` = www.okmentor.in

Most people use `@` for simplicity.

### Q: Can I use www?

Yes! You can add multiple CNAME records:

```
@ points to app.nextslot.in
www points to app.nextslot.in
```

This way both okmentor.in and www.okmentor.in work.

### Q: How long does DNS take?

Usually 5-30 minutes. Sometimes up to 24 hours.

If it's been more than an hour:
1. Check you entered the record correctly
2. Wait a bit more (DNS can be slow)
3. Clear your browser cache (Ctrl+F5)
4. Try a different browser
5. Contact support if stuck

### Q: What if it says the domain already exists?

It might show "The value you entered is not allowed (duplicate)" or similar.

This is normal! It just means someone is already using that CNAME. Contact support.

### Q: Is this secure?

Yes! Your custom domain:
- Has a free SSL certificate (encrypted connection)
- Is served by our secure servers
- Has all the same security as our website

You'll see the green lock 🔒 in your browser, meaning it's secure.

### Q: Can I change it back?

Yes! You can remove the CNAME record anytime from your registrar.

But we hope you'll keep it - your custom domain looks professional! 😊

### Q: Will my email work?

No, this CNAME record is just for your booking website.

Email is separate (MX records). Contact your registrar about email setup.

### Q: Can I use my own SSL certificate?

Yes, but you don't need to! You get a free one automatically.

If you want to use your own, contact support - we can configure it.

### Q: What if I need help?

**Contact us:**
- Email: support@nextslot.in
- Chat: In your NextSlot dashboard
- Phone: [Your support number]

We're here to help! 😊

---

## Checklist

- [ ] Found your domain registrar
- [ ] Signed in to your registrar account
- [ ] Added CNAME record:
  - [ ] Type: CNAME
  - [ ] Name: @
  - [ ] Value: app.nextslot.in
- [ ] Clicked Save
- [ ] Waiting for DNS (come back in 5-30 minutes)
- [ ] Checked status on mxtoolbox.com
- [ ] Domain is working! 🎉

---

## Next Steps

1. **Add the CNAME record now** (5 minutes)
2. **Wait for DNS** (5-30 minutes)
3. **Check it's working** (mxtoolbox.com)
4. **Visit your domain** (https://yourdomainname.com)
5. **See your booking page** ✅

---

## We're Here to Help!

If you get stuck at any point:

1. **Check the FAQ above** - Most issues are covered
2. **Contact support** - We'll help you through it
3. **Provide these details:**
   - Your domain name
   - Your registrar name
   - Screenshot of DNS record (if possible)

We'll get you sorted! 🚀

---

**Once your DNS is setup, your custom domain will be live!**

Your booking page will be at: `https://yourdomainname.com` 🎉

Congratulations on your professional custom domain! 

- NextSlot Team 💙
