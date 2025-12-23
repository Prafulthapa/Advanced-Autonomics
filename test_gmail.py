#!/usr/bin/env python3
"""
Test Gmail SMTP connection
Run this BEFORE starting Docker to verify credentials work
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail credentials
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "ygauli@gmail.com"
SMTP_PASSWORD = "lipk mywo qvcy dtxq"  # App password with spaces
FROM_EMAIL = "ygauli@gmail.com"

# Test email (send to yourself)
TO_EMAIL = "ygauli@gmail.com"  # Change to test email if needed

def test_gmail():
    """Test Gmail SMTP connection and sending."""
    print("🧪 Testing Gmail SMTP connection...")
    print(f"📧 SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
    print(f"👤 User: {SMTP_USER}")
    print(f"📨 Sending test email to: {TO_EMAIL}")
    print()
    
    try:
        # Create test message
        msg = MIMEMultipart()
        msg['Subject'] = "Test Email - Advanced Autonomics System"
        msg['From'] = f"Advanced Autonomics <{FROM_EMAIL}>"
        msg['To'] = TO_EMAIL
        
        body = """
Hello!

This is a test email from the Advanced Autonomics AI Agent system.

If you received this, your Gmail SMTP configuration is working correctly! ✓

Next steps:
1. Start the Docker system: docker-compose up -d
2. Check agent status: curl http://localhost:8000/agent/status
3. Import leads and start agent

Best regards,
Advanced Autonomics AI Agent
"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail
        print("📡 Connecting to Gmail SMTP...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.set_debuglevel(0)
        
        print("🔐 Starting TLS...")
        server.starttls()
        
        print("🔑 Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        
        print("📤 Sending test email...")
        server.send_message(msg)
        
        print("✅ SUCCESS! Email sent successfully!")
        print(f"📬 Check {TO_EMAIL} for the test email")
        print()
        print("✓ Gmail SMTP is working correctly")
        print("✓ You can now start the production system")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("❌ AUTHENTICATION FAILED!")
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Make sure 2FA is enabled on ygauli@gmail.com")
        print("2. Generate new App Password at: https://myaccount.google.com/apppasswords")
        print("3. Copy app password EXACTLY (with spaces is OK)")
        print("4. Update .env file with new password")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check internet connection")
        print("2. Verify Gmail IMAP is enabled")
        print("3. Try again in a few minutes")
        return False

if __name__ == "__main__":
    test_gmail()