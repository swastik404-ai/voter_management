import os
import logging
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from email.mime.application import MIMEApplication
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailService:
    @staticmethod
    def send_email_with_attachment(to_email, subject, template_name, context, pdf_path=None):
        try:
            logger.info(f"Attempting to send email to {to_email}")

            # Create MIME message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = to_email

            # Render HTML content
            html_content = render_to_string(template_name, context)
            msg.attach(MIMEText(html_content, 'html'))

            # Attach PDF if provided
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as pdf_file:
                    pdf_part = MIMEApplication(pdf_file.read(), _subtype='pdf')
                    pdf_part.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(pdf_path)
                    )
                    msg.attach(pdf_part)

            # Connect to SMTP server
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                server.starttls()
                logger.info("Established SMTP connection")

                # Login
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                logger.info("SMTP login successful")

                # Send email
                server.send_message(msg)
                logger.info(f"Email sent successfully to {to_email}")

                return True, "Email sent successfully"

        except smtplib.SMTPAuthenticationError as e:
            error_msg = "SMTP Authentication failed. Please check email credentials."
            logger.error(f"{error_msg}: {str(e)}")
            return False, error_msg

        except smtplib.SMTPException as e:
            error_msg = f"SMTP Error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg