#!/usr/bin/env python3
"""
Test HTML email sending with images
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.email_service import EmailService
from app.services.html_email_templates import get_html_template

def test_html_email():
    """Send a test HTML email to yourself."""
    
    print("🧪 Testing HTML Email with Images\n")
    
    # Test data
    test_email = "girihemraj94@gmail.com "  # Send to yourself for testing
    test_first_name = "Yudhistir"
    test_last_name = "Gauli"
    test_company = "Test Industries Inc."
    
    # Generate HTML email
    html_body, images = get_html_template(
    first_name=test_first_name,
    last_name=test_last_name,
    company=test_company,
    email=test_email,
    industry="Glassworks",
    from_email="contact@advanced-autonomics.com"
    )
    
    # Add unsubscribe link
    html_body = html_body.replace(
        "{{unsubscribe_link}}", 
        "http://localhost:8000/unsubscribe?email=" + test_email
    )
    
    # Plain text fallback
    plain_text = f"""
Hi {test_first_name},

This is a test email from Advanced Autonomics.

If you can see this, your email client doesn't support HTML emails.
Please view in a modern email client to see the full formatted version.

Best regards,
Advanced Autonomics Team
"""
    
    # Check if logo exists
    logo_path = "app/static/images/logo.png"
    if not os.path.exists(logo_path):
        print(f"⚠️ WARNING: Logo not found at {logo_path}")
        print("   Run create_logo_placeholder.py first, or add your own logo")
        print()
        
        create = input("Create placeholder logo now? (y/n): ")
        if create.lower() == 'y':
            from create_logo_placeholder import create_placeholder_logo
            create_placeholder_logo()
        else:
            print("❌ Cannot send email without logo. Exiting.")
            return
    
    # Send email
    print(f"📧 Sending HTML test email to: {test_email}")
    print(f"📎 Embedding images: {list(images.keys())}")
    print()
    
    success, error = EmailService.send_email(
        to_email=test_email,
        subject="🤖 Test HTML Email - Advanced Autonomics",
        body=plain_text,
        to_name=f"{test_first_name} {test_last_name}",
        html_body=html_body,
        images=images
    )
    
    if success:
        print("✅ SUCCESS! HTML email sent!")
        print()
        print("📬 Check your inbox for:")
        print(f"   To: {test_email}")
        print("   Subject: 🤖 Test HTML Email - Advanced Autonomics")
        print()
        print("What to check:")
        print("   1. Does the logo appear at the top?")
        print("   2. Is the formatting nice and professional?")
        print("   3. Are colors showing correctly?")
        print("   4. Do links work?")
        print()
        print("If everything looks good, you're ready to send to real leads! 🚀")
    else:
        print(f"❌ FAILED: {error}")
        print()
        print("Troubleshooting:")
        print("   1. Check SMTP credentials in .env")
        print("   2. Verify logo file exists")
        print("   3. Check Gmail app password")

if __name__ == "__main__":
    test_html_email()