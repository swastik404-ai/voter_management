import os
import sys
import django
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('email_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def test_email_connection():
    try:
        # Email settings
        smtp_server = "smtp.gmail.com"
        port = 587
        sender_email = "captainsparrow2814@gmail.com"
        password = "kzwe emau uowy gyzw"  # Your app password

        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = "Test Email"
        msg['From'] = sender_email
        msg['To'] = sender_email

        # Add body
        body = f"""
        This is a test email
        Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        From: Temple Pass System
        """
        msg.attach(MIMEText(body, 'plain'))

        logger.info("Attempting to connect to SMTP server...")

        # Create server object with debugging
        server = smtplib.SMTP(smtp_server, port)
        server.set_debuglevel(1)  # Enable debug output

        logger.info("Starting TLS...")
        server.starttls()

        # Login
        logger.info("Attempting to login...")
        server.login(sender_email, password)

        # Send email
        logger.info("Sending email...")
        server.send_message(msg)

        logger.info("Email sent successfully!")
        server.quit()

        return True, "Email sent successfully"

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


if __name__ == "__main__":
    success, message = test_email_connection()
    print(f"\nResult: {'Success' if success else 'Failed'}")
    print(f"Message: {message}")