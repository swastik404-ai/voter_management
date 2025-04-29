import os
import logging
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage, get_connection
from datetime import datetime
from django.utils import timezone


logger = logging.getLogger('passes')


def generate_pass_pdf(pass_obj):
    """Generate PDF pass from the template"""
    try:
        # Format the date for letter number
        letter_date = pass_obj.processed_at.strftime('%d-%m-%Y')
        letter_number = f"Lr. No: {pass_obj.id:03d}/{pass_obj.temple}/{letter_date}"

        # Prepare context for the pass template
        context = {
            'letter_number': letter_number,
            'name': pass_obj.name,
            'phone': pass_obj.phone,
            'id_proof_number': pass_obj.id_proof_number,
            'temple': pass_obj.temple,
            'visit_date': pass_obj.visit_date.strftime('%d-%m-%Y'),
            'num_persons': pass_obj.num_persons,
            'processed_date': letter_date,
            # Add static image URLs
            'satyameva_jayate_img': os.path.join(settings.STATIC_URL, 'images/Satyameva-Jayate.png'),
            'signature_img': os.path.join(settings.STATIC_URL, 'images/signature.png'),
        }

        logger.debug(f"Generating PDF for pass ID: {pass_obj.id}")

        # Render the HTML template
        template_path = 'passes/pass_template.html'
        html_content = render_to_string(template_path, context)

        # Generate PDF
        pdf = HTML(string=html_content, base_url=settings.STATIC_URL).write_pdf()

        # Create filename for the PDF
        filename = f"temple_pass_{pass_obj.id}_{pass_obj.temple}_{letter_date}.pdf"
        pdf_path = os.path.join(settings.TEMP_DIR, filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

        # Save PDF
        with open(pdf_path, 'wb') as f:
            f.write(pdf)

        logger.info(f"Successfully generated PDF at {pdf_path}")
        return pdf_path, filename

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise


def send_email_with_pdf(pass_obj, action, additional_message=None):
    """Send email with PDF attachment"""
    try:
        logger.debug(f"Preparing to send email for pass ID: {pass_obj.id}")

        context = {
            'name': pass_obj.name,
            'temple': pass_obj.temple,
            'visit_date': pass_obj.visit_date.strftime('%Y-%m-%d'),
            'num_persons': pass_obj.num_persons,
            'id_proof_type': pass_obj.get_id_proof_type_display(),
            'id_proof_number': pass_obj.id_proof_number,
            'status': action.upper(),
            'processed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'processed_by': pass_obj.processed_by.username if pass_obj.processed_by else 'Admin',
            'additional_message': additional_message,
        }

        template_name = (
            'passes/email_templates/pass_approved.html'
            if action.upper() == 'APPROVED'
            else 'passes/email_templates/pass_rejected.html'
        )

        subject = (
            'Temple Pass Request Approved'
            if action.upper() == 'APPROVED'
            else 'Temple Pass Request Rejected'
        )

        # Render email template
        html_message = render_to_string(template_name, context)

        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[pass_obj.email]
        )
        email.content_subtype = "html"

        # If approved, attach PDF
        if action.upper() == 'APPROVED':
            try:
                pdf_path, pdf_filename = generate_pass_pdf(pass_obj)
                logger.debug(f"Attaching PDF: {pdf_path}")

                with open(pdf_path, 'rb') as f:
                    email.attach(pdf_filename, f.read(), 'application/pdf')

                # Clean up temporary file
                os.remove(pdf_path)
                logger.debug(f"Cleaned up temporary PDF file: {pdf_path}")

            except Exception as e:
                logger.error(f"Error handling PDF attachment: {str(e)}", exc_info=True)
                raise

        # Get SMTP connection
        connection = get_connection(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS
        )

        # Send email
        logger.debug(f"Attempting to send email to {pass_obj.email}")
        email.connection = connection
        email.send(fail_silently=False)

        logger.info(f"Successfully sent email to {pass_obj.email}")
        return True, "Email sent successfully"

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg