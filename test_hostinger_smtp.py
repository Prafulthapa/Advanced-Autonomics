#!/usr/bin/env python3
"""
Test Hostinger SMTP Connection
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Hostinger credentials
SMTP_HOST = "smtp.hostinger.com"
SMTP_PORT = 465
SMTP_USER = "sarah@advanced-autonomics.com"
SMTP_PASSWORD = "UM^BCXg|!u5*76"
FROM_EMAIL = "sarah@advanced-autonomics.com"

# Send to yourself for testing
TO_EMAIL = "prafulthapa339@gmail.com"

def test_hostinger():
    print("🧪 Testing Hostinger SMTP connection...")
    print(f"📧 SMTP Server: {SMTP_HOST}:{SMTP_PORT}")
    print(f"👤 User: {SMTP_USER}")
    print(f"📨 Sending test email to: {TO_EMAIL}")
    print()

    try:
        # Create test message
        msg = MIMEMultipart()
        msg['Subject'] = "Test Email - Advanced Autonomics System"
        msg['From'] = f"Sarah - Advanced Autonomics <{FROM_EMAIL}>"
        msg['To'] = TO_EMAIL

        body = """
Hello!

This is a test email from the Advanced Autonomics AI Agent system using Hostinger email.

If you received this, your Hostinger SMTP configuration is working correctly! ✓

Next steps:
1. Verify IMAP is working (test_hostinger_imap.py)
2. Start the Docker system: docker-compose up -d
3. Check agent status: curl http://localhost:8000/agent/status

Best regards,
Sarah - Advanced Autonomics AI Agent
"""
        msg.attach(MIMEText(body, 'plain'))

        # Connect to Hostinger with SSL
        print("🔐 Connecting to Hostinger SMTP (SSL)...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        server.set_debuglevel(1)  # Show detailed connection info

        print("🔑 Logging in...")
        server.login(SMTP_USER, SMTP_PASSWORD)

        print("📤 Sending test email...")
        server.send_message(msg)

        print("\n✅ SUCCESS! Email sent successfully!")
        print(f"📬 Check {TO_EMAIL} for the test email")
        print()
        print("✓ Hostinger SMTP is working correctly")

        server.quit()
        return True

    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ AUTHENTICATION FAILED!")
        print(f"Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Verify email: sarah@advanced-autonomics.com")
        print("2. Verify password: UM^BCXg|!u5*76")
        print("3. Check if email account is active in Hostinger")
        print("4. Ensure SMTP is enabled in Hostinger settings")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Check internet connection")
        print("2. Verify smtp.hostinger.com is reachable")
        print("3. Check firewall settings")
        return False

if __name__ == "__main__":
    test_hostinger()