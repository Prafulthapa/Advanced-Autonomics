import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Email configuration - Production Gmail
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SMTP_USER = os.getenv("SMTP_USER", "ygauli@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "ygauli@gmail.com")
FROM_NAME = os.getenv("FROM_NAME", "Advanced Autonomics")


class EmailService:

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        body: str,
        to_name: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Send an email via Gmail SMTP.
        Returns: (success: bool, error_message: Optional[str])
        """
        try:
            logger.info(f"Sending email to {to_email} via {SMTP_HOST}:{SMTP_PORT}")

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg['To'] = f"{to_name} <{to_email}>" if to_name else to_email
            
            # Add Reply-To header (important for tracking replies)
            msg['Reply-To'] = FROM_EMAIL

            # Add body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Connect and send via Gmail
            if SMTP_USE_TLS:
                # TLS connection (port 587)
                with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                    server.set_debuglevel(0)  # Set to 1 for debugging
                    server.starttls()  # Upgrade to TLS
                    
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                        logger.info(f"✓ Logged in to Gmail as {SMTP_USER}")
                    
                    server.send_message(msg)
            else:
                # SSL connection (port 465) - alternative
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                    if SMTP_USER and SMTP_PASSWORD:
                        server.login(SMTP_USER, SMTP_PASSWORD)
                    
                    server.send_message(msg)

            logger.info(f"✓ Email sent successfully to {to_email}")
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"Gmail authentication failed: {str(e)}"
            logger.error(error_msg)
            logger.error("Check: 1) App password is correct, 2) 2FA is enabled, 3) Less secure apps is disabled")
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error sending email: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return False, error_msg

    @staticmethod
    def generate_subject(lead_name: str, company: str) -> str:
        """
        Generate a subject line for cold email.
        """
        if company:
            return f"Quick question about {company}'s outreach"
        return f"Quick question for you, {lead_name}"