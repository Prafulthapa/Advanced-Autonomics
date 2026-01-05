#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.services.email_service import EmailService
from app.services.html_email_templates_professional import get_full_professional_template

# Test data
test_email = "ygauli@gmail.com"  # Change to your email
test_first_name = "ygaulisir"
test_company = "Test Industries Inc."

print("🧪 Testing FULL Professional HTML Email\n")

# Generate email
html_body, images = get_full_professional_template(
    first_name=test_first_name,
    company=test_company,
    email=test_email
)

print(f"📧 Sending to: {test_email}")
print(f"📎 Images: {list(images.keys())}")

# Check all images exist
import os
all_exist = True
for cid, path in images.items():
    if os.path.exists(path):
        size = os.path.getsize(path) / 1024
        print(f"   ✅ {cid}: {path} ({size:.1f} KB)")
    else:
        print(f"   ❌ {cid}: {path} NOT FOUND")
        all_exist = False

if not all_exist:
    print("\n❌ Some images are missing! Cannot send email.")
    sys.exit(1)

print("\n📤 Sending email...")

# Plain text fallback
plain_text = f"""Hi {test_first_name},

This is a test email from Advanced Autonomics.

We're offering no-cost pilot installations of our Robocrafter Series AMR.

Best regards,
Advanced Autonomics Team
"""

# Send
success, error = EmailService.send_email(
    to_email=test_email,
    subject="🤖 Advanced Autonomics - No-Cost Pilot Program",
    body=plain_text,
    to_name=f"{test_first_name}",
    html_body=html_body,
    images=images
)

if success:
    print("\n✅ SUCCESS! Email sent!")
    print(f"📬 Check your inbox: {test_email}")
    print("\nWhat to check:")
    print("   1. Does the email look professional?")
    print("   2. Are all images showing?")
    print("   3. Do buttons work?")
    print("   4. Does it look good on mobile?")
else:
    print(f"\n❌ FAILED: {error}")