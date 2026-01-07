from dotenv import load_dotenv
load_dotenv()
import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
import os
from typing import Optional, Dict
from datetime import datetime
import time
import socket

logger = logging.getLogger(__name__)

# ============================================
# Email configuration - Supports Gmail & Hostinger
# ============================================
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.hostinger.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"

SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Advanced Autonomics")

# IMAP configuration for saving to Sent folder
IMAP_HOST = os.getenv("IMAP_HOST", "imap.hostinger.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))
IMAP_USERNAME = os.getenv("IMAP_USERNAME", SMTP_USER)
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", SMTP_PASSWORD)

logger.info(f"📧 Email Service Config:")
logger.info(f"   SMTP: {SMTP_HOST}:{SMTP_PORT} (TLS: {SMTP_USE_TLS}, SSL: {SMTP_USE_SSL})")
logger.info(f"   IMAP: {IMAP_HOST}:{IMAP_PORT}")
logger.info(f"   From: {FROM_NAME} <{FROM_EMAIL}>")


# ============================================
# 🔧 SAFETY CHECK — PREVENT INVALID SMTP CONFIG
# ============================================

if SMTP_USE_SSL and SMTP_PORT != 465:
    raise ValueError(
        "Invalid SMTP config: SMTP_USE_SSL=true requires SMTP_PORT=465"
    )

if SMTP_USE_TLS and SMTP_PORT != 587:
    raise ValueError(
        "Invalid SMTP config: SMTP_USE_TLS=true requires SMTP_PORT=587"
    )

if SMTP_USE_SSL and SMTP_USE_TLS:
    raise ValueError(
        "Invalid SMTP config: Cannot enable both SSL and TLS at the same time"
    )

class EmailService:

    @staticmethod
    def save_to_sent_folder(msg: MIMEMultipart) -> bool:
        """
        Save sent message to IMAP Sent folder.
        Required for Hostinger since SMTP doesn't auto-save.
        """
        mail = None
        try:
            logger.info("💾 Saving to Sent folder via IMAP...")
            
            # Connect to IMAP with timeout
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.sock.settimeout(30)  # 30 second timeout
            mail.login(IMAP_USERNAME, IMAP_PASSWORD)
            
            # Common Sent folder names (try in order)
            sent_folders = ["Sent", "INBOX.Sent", "[Gmail]/Sent Mail", "Sent Messages"]
            
            # List available folders
            status, folders = mail.list()
            available = [f.decode().split('"')[-2] for f in folders] if status == "OK" else []
            
            # Find the Sent folder
            sent_folder = None
            for folder in sent_folders:
                if folder in available:
                    sent_folder = folder
                    break
            
            if not sent_folder and available:
                for folder in available:
                    if "sent" in folder.lower():
                        sent_folder = folder
                        break
            
            if not sent_folder:
                sent_folder = "INBOX"
            
            logger.info(f"📤 Saving to: {sent_folder}")
            
            # Add Date header if missing
            if not msg.get("Date"):
                msg["Date"] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            # Append message to Sent folder
            mail.append(
                sent_folder,
                "\\Seen",
                imaplib.Time2Internaldate(time.time()),
                msg.as_bytes()
            )
            
            logger.info("✅ Message saved to Sent folder")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Sent folder: {e}")
            return False
        finally:
            if mail:
                try:
                    mail.logout()
                except:
                    pass

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None,
        html_body: Optional[str] = None,
        images: Optional[Dict[str, str]] = None,
        attachments: Optional[list] = None,
        save_to_sent: bool = True
    ) -> tuple[bool, Optional[str]]:
        """
        Send HTML email with embedded images via SMTP.
        Uses fresh connection for each email (prevents timeout issues).
        """
        server = None
        try:
            logger.info(f"📤 Preparing email to {to_email}")

            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            msg['Reply-To'] = FROM_EMAIL
            msg['Date'] = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

            # Create alternative container
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # Add plain text
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg_alternative.attach(text_part)

            # Add HTML
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg_alternative.attach(html_part)

            # Embed images
            if images:
                for cid, image_path in images.items():
                    if os.path.exists(image_path):
                        try:
                            with open(image_path, 'rb') as img_file:
                                img_data = img_file.read()
                                
                                if image_path.lower().endswith('.png'):
                                    img = MIMEImage(img_data, 'png')
                                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                                    img = MIMEImage(img_data, 'jpeg')
                                else:
                                    img = MIMEImage(img_data)
                                
                                img.add_header('Content-ID', f'<{cid}>')
                                img.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                                msg.attach(img)
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to embed {cid}: {e}")

            # ============================================
            # Send via SMTP - FRESH CONNECTION each time
            # ============================================
            
            if SMTP_USE_SSL:
                # SSL connection (Hostinger, port 465)
                logger.info(f"🔐 Creating fresh SSL connection to {SMTP_HOST}:{SMTP_PORT}")
                
                # Create connection with explicit timeout
                server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30)
                server.set_debuglevel(0)
                
                # Set socket timeout
                if server.sock:
                    server.sock.settimeout(30)
                
                # Login
                if SMTP_USER and SMTP_PASSWORD:
                    logger.info(f"🔑 Authenticating as {SMTP_USER}")
                    server.login(SMTP_USER, SMTP_PASSWORD)
                
                # Send message
                logger.info(f"📨 Sending message...")
                server.send_message(msg)
                logger.info(f"✅ SMTP send successful")
                
                # Explicitly close connection
                server.quit()
                server = None
                    
            elif SMTP_USE_TLS:
                # TLS connection (Gmail, port 587)
                logger.info(f"🔐 Creating fresh TLS connection to {SMTP_HOST}:{SMTP_PORT}")
                
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                server.set_debuglevel(0)
                
                if server.sock:
                    server.sock.settimeout(30)
                
                server.starttls()
                
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                
                server.send_message(msg)
                logger.info(f"✅ SMTP send successful")
                
                server.quit()
                server = None
                
            else:
                # Plain SMTP
                logger.warning("⚠️ Using plain SMTP (no encryption)")
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                
                server.send_message(msg)
                server.quit()
                server = None

            # ============================================
            # Save to Sent folder (separate connection)
            # ============================================
            if save_to_sent and IMAP_HOST and IMAP_USERNAME:
                # Small delay to ensure SMTP completed
                time.sleep(1)
                EmailService.save_to_sent_folder(msg)

            logger.info(f"✅ Email successfully delivered to {to_email}")
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        except smtplib.SMTPServerDisconnected as e:
            error_msg = f"Server disconnected: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        except socket.timeout as e:
            error_msg = f"Connection timeout: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
            
        finally:
            # Ensure connection is closed
            if server:
                try:
                    server.quit()
                except:
                    try:
                        server.close()
                    except:
                        pass

    @staticmethod
    def generate_subject(lead_name: str, company: str) -> str:
        """Generate subject line."""
        if company:
            return f"Pilot Opportunity: Autonomous Handling for {company}"
        return f"Automation Opportunity for {lead_name}"