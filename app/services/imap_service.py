import imaplib
import email
from email.header import decode_header
from datetime import datetime
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

# ============================================
# ✅ FIXED: IMAP Configuration (Hostinger)
# ============================================
IMAP_HOST = os.getenv("IMAP_HOST", "imap.hostinger.com")  # ✅ Changed default
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))  # ✅ Changed default
IMAP_USERNAME = os.getenv("IMAP_USERNAME")  # ✅ Changed from IMAP_USER
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD")
IMAP_USE_SSL = os.getenv("IMAP_USE_SSL", "true").lower() == "true"  # ✅ Changed default

# Debug logging
logger.info(f"📧 IMAP Config: {IMAP_HOST}:{IMAP_PORT} (SSL: {IMAP_USE_SSL})")
logger.info(f"👤 IMAP User: {IMAP_USERNAME}")


class IMAPService:
    """Service for fetching and parsing emails via IMAP."""

    @staticmethod
    def connect() -> imaplib.IMAP4:
        """Establish IMAP connection."""
        try:
            if IMAP_USE_SSL:
                logger.info(f"🔐 Connecting to IMAP (SSL) at {IMAP_HOST}:{IMAP_PORT}")
                mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            else:
                logger.info(f"📡 Connecting to IMAP at {IMAP_HOST}:{IMAP_PORT}")
                mail = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)

            # Login if credentials provided
            if IMAP_USERNAME and IMAP_PASSWORD:
                logger.info(f"🔑 Logging in as {IMAP_USERNAME}")
                mail.login(IMAP_USERNAME, IMAP_PASSWORD)
                logger.info(f"✅ Logged in successfully")
            else:
                logger.error("❌ IMAP credentials not provided")
                raise Exception("IMAP_USERNAME or IMAP_PASSWORD not set")

            return mail

        except imaplib.IMAP4.error as e:
            logger.error(f"❌ IMAP authentication failed: {str(e)}")
            logger.error(f"   Host: {IMAP_HOST}:{IMAP_PORT}")
            logger.error(f"   User: {IMAP_USERNAME}")
            logger.error(f"   SSL: {IMAP_USE_SSL}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to connect to IMAP: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def decode_header_value(header_value: str) -> str:
        """Decode email header value."""
        if not header_value:
            return ""

        decoded_parts = decode_header(header_value)
        result = []

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='ignore'))
            else:
                result.append(str(part))

        return ' '.join(result)

    @staticmethod
    def extract_email_address(header_value: str) -> str:
        """Extract email address from header like 'Name <email@domain.com>'."""
        if not header_value:
            return ""

        # Simple extraction - look for <email@domain.com> pattern
        if '<' in header_value and '>' in header_value:
            start = header_value.index('<') + 1
            end = header_value.index('>')
            return header_value[start:end].strip().lower()

        return header_value.strip().lower()

    @staticmethod
    def get_email_body(msg: email.message.Message) -> str:
        """Extract email body (plain text preferred)."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                # Get plain text
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except Exception as e:
                        logger.warning(f"Failed to decode text/plain: {e}")
                        continue

                # Fallback to HTML if no plain text
                if content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except Exception as e:
                        logger.warning(f"Failed to decode text/html: {e}")
        else:
            # Not multipart - get payload directly
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except Exception as e:
                logger.warning(f"Failed to decode body: {e}")
                body = str(msg.get_payload())

        return body.strip()

    @staticmethod
    def fetch_unread_emails(limit: int = 50) -> List[Dict]:
        """
        Fetch unread emails from inbox.
        Returns list of parsed email dictionaries.
        """
        emails = []
        mail = None

        try:
            mail = IMAPService.connect()
            mail.select("INBOX")

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")

            if status != "OK":
                logger.warning("No unread messages found")
                return emails

            email_ids = messages[0].split()
            logger.info(f"📬 Found {len(email_ids)} unread emails")

            # Process most recent emails first (limit)
            for email_id in email_ids[-limit:]:
                try:
                    # Fetch email
                    status, msg_data = mail.fetch(email_id, "(RFC822)")

                    if status != "OK":
                        logger.warning(f"Failed to fetch email {email_id}")
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract headers
                    from_header = msg.get("From", "")
                    to_header = msg.get("To", "")
                    subject_header = msg.get("Subject", "")
                    message_id = msg.get("Message-ID", "")
                    in_reply_to = msg.get("In-Reply-To", "")
                    references = msg.get("References", "")
                    date_header = msg.get("Date", "")

                    # Decode headers
                    from_email = IMAPService.extract_email_address(
                        IMAPService.decode_header_value(from_header)
                    )
                    to_email = IMAPService.extract_email_address(
                        IMAPService.decode_header_value(to_header)
                    )
                    subject = IMAPService.decode_header_value(subject_header)

                    # Extract body
                    body = IMAPService.get_email_body(msg)

                    # Parse date
                    received_at = None
                    if date_header:
                        try:
                            received_at = email.utils.parsedate_to_datetime(date_header)
                        except Exception as e:
                            logger.warning(f"Failed to parse date: {e}")

                    # Store parsed email
                    parsed_email = {
                        "from_email": from_email,
                        "to_email": to_email,
                        "subject": subject,
                        "body": body,
                        "message_id": message_id,
                        "in_reply_to": in_reply_to,
                        "references": references,
                        "received_at": received_at,
                        "raw_headers": str(msg.items())
                    }

                    emails.append(parsed_email)
                    logger.info(f"✅ Parsed email from {from_email}")

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}", exc_info=True)
                    continue

            logger.info(f"✅ Successfully fetched {len(emails)} emails")
            return emails

        except Exception as e:
            logger.error(f"❌ Error fetching emails: {str(e)}", exc_info=True)
            return emails

        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except:
                    pass