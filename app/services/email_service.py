from dotenv import load_dotenv
load_dotenv()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import logging
import os
from typing import Optional, Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Email configuration - Production Gmail
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

SMTP_USER = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "Advanced Autonomics")

# 🔎 DEBUG PROOF CHECK (temporary)
logger.warning(f"SMTP_USERNAME loaded: {SMTP_USER}")
logger.warning(f"SMTP_PASSWORD loaded: {bool(SMTP_PASSWORD)}")

class EmailService:

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None,
        html_body: Optional[str] = None,
        images: Optional[Dict[str, str]] = None,
        attachments: Optional[list] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send HTML email with embedded images via Gmail SMTP.
        FIXED: Proper MIME structure for Gmail HTML rendering.
        """
        try:
            logger.info(f"Sending email to {to_email}")

            # Create message with 'related' for embedded images
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            msg['Reply-To'] = FROM_EMAIL

            # Create 'alternative' container for text/html versions
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            # CRITICAL: Add plain text FIRST (fallback)
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg_alternative.attach(text_part)

            # Add HTML version SECOND (preferred)
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg_alternative.attach(html_part)
                logger.info("✅ HTML body attached")

            # Embed images AFTER text/html parts
            if images:
                for cid, image_path in images.items():
                    if os.path.exists(image_path):
                        try:
                            with open(image_path, 'rb') as img_file:
                                img_data = img_file.read()
                                
                                # Detect image type
                                if image_path.lower().endswith('.png'):
                                    img = MIMEImage(img_data, 'png')
                                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                                    img = MIMEImage(img_data, 'jpeg')
                                else:
                                    img = MIMEImage(img_data)
                                
                                # CRITICAL: Set Content-ID for inline display
                                img.add_header('Content-ID', f'<{cid}>')
                                img.add_header('Content-Disposition', 'inline', filename=os.path.basename(image_path))
                                msg.attach(img)
                                
                                logger.info(f"✅ Embedded: {cid} ({len(img_data)/1024:.1f}KB)")
                        except Exception as e:
                            logger.error(f"❌ Failed to embed {cid}: {e}")
                    else:
                        logger.warning(f"⚠️ Image not found: {image_path}")

            # Connect and send
            if SMTP_USE_TLS:
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                    server.set_debuglevel(0)
                    server.starttls()
                    
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                        logger.info(f"✅ Logged in as {SMTP_USER}")
                    
                    server.send_message(msg)
                    logger.info(f"✅ Email sent to {to_email}")
            else:
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                    server.send_message(msg)

            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Gmail authentication failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    @staticmethod
    def generate_subject(lead_name: str, company: str) -> str:
        """Generate subject line."""
        if company:
            return f"Pilot Opportunity: Autonomous Handling for {company}"
        return f"Automation Opportunity for {lead_name}"

