#!/usr/bin/env python3
"""
Test IMAP connection directly
"""

import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USERNAME = os.getenv("IMAP_USERNAME")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")

print("🧪 Testing IMAP Connection")
print(f"📧 Host: {IMAP_HOST}:{IMAP_PORT}")
print(f"👤 User: {IMAP_USERNAME}")
print()

try:
    print("🔐 Connecting with SSL...")
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    
    print("🔑 Logging in...")
    mail.login(IMAP_USERNAME, IMAP_PASSWORD)
    
    print("✅ LOGIN SUCCESS!")
    
    print("\n📬 Checking inbox...")
    status, mailbox_data = mail.select("INBOX")
    
    if status == "OK":
        num_messages = int(mailbox_data[0])
        print(f"✅ Inbox has {num_messages} messages")
        
        # Check for unread
        status, unread_data = mail.search(None, "UNSEEN")
        if status == "OK":
            unread_ids = unread_data[0].split()
            print(f"📨 {len(unread_ids)} unread messages")
    
    mail.logout()
    print("\n✅ IMAP CONNECTION TEST PASSED!")
    print("Your credentials are working correctly.")
    
except imaplib.IMAP4.error as e:
    print(f"\n❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Make sure IMAP is enabled in Gmail settings")
    print("2. Check if the app password is correct")
    print("3. Try generating a new app password")
    print("4. Make sure you're using the Gmail account password, not regular password")
    
except Exception as e:
    print(f"\n❌ CONNECTION ERROR!")
    print(f"Error: {e}")
    print("\n🔧 Check:")
    print("1. Internet connection")
    print("2. IMAP host and port are correct")
    print("3. Firewall settings")