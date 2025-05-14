from django.contrib import admin
from django.utils import timezone
from django.http import JsonResponse
from django.urls import path
from django.utils.timezone import localtime
from .models import Pass
import logging
from datetime import datetime
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os
from .email_service import EmailService
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML

logger = logging.getLogger(__name__)


@admin.register(Pass)
class PassAdmin(admin.ModelAdmin):
    change_list_template = "admin/passes/pass/change_list.html"

    list_display = []
    list_filter = []

    search_fields = ['name', 'email', 'phone', 'id_proof_number']
    readonly_fields = ['created_at', 'updated_at', 'processed_at', 'processed_by']
    ordering = ['-created_at']



    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'api/passes/pending/',
                self.admin_site.admin_view(self.get_pending_passes),
                name='api-pending-passes'
            ),
            path(
                'api/passes/approved/',
                self.admin_site.admin_view(self.get_approved_passes),
                name='api-approved-passes'
            ),
            path(
                'api/passes/rejected/',
                self.admin_site.admin_view(self.get_rejected_passes),
                name='api-rejected-passes'
            ),
            path(
                'api/passes/<int:pass_id>/approve/',
                self.admin_site.admin_view(self.approve_pass),
                name='api-approve-pass'
            ),
            path(
                'api/passes/<int:pass_id>/reject/',
                self.admin_site.admin_view(self.reject_pass),
                name='api-reject-pass'
            ),
            path(
                'api/passes/bulk-reject/',
                self.admin_site.admin_view(self.bulk_reject_passes),
                name='api-bulk-reject-passes'
            ),
            path(
                'api/passes/bulk-delete/',
                self.admin_site.admin_view(self.bulk_delete_passes),
                name='api-bulk-delete-passes'
            ),
            path(
                'api/passes/counts/',
                self.admin_site.admin_view(self.get_pass_counts),
                name='api-pass-counts'
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        # Get unique temples and dates for filters
        temples = Pass.objects.values_list('temple', flat=True).distinct().order_by('temple')

        # Apply filters to counts if present
        filter_params = {}
        if 'temple' in request.GET:
            filter_params['temple'] = request.GET['temple']
        if 'date' in request.GET:
            filter_params['visit_date'] = request.GET['date']

        pending_count = Pass.objects.filter(status='PENDING', **filter_params).count()
        approved_count = Pass.objects.filter(status='APPROVED', **filter_params).count()
        rejected_count = Pass.objects.filter(status='REJECTED', **filter_params).count()

        extra_context = extra_context or {}
        extra_context.update({
            'title': 'Pass Management',
            'temples': temples,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'current_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_user': request.user.username,
            'status_filter': request.GET.get('status_filter', 'PENDING'),
        })
        return super().changelist_view(request, extra_context=extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        temple = request.GET.get('temple')
        date = request.GET.get('date')

        if temple:
            qs = qs.filter(temple=temple)
        if date:
            qs = qs.filter(visit_date=date)
        return qs

    def get_pass_data(self, pass_obj):
        return {
            'id': pass_obj.id,
            'name': pass_obj.name,
            'email': pass_obj.email,
            'phone': pass_obj.phone,
            'temple': pass_obj.temple,
            'visit_date': pass_obj.visit_date.strftime('%Y-%m-%d'),
            'num_persons': pass_obj.num_persons,
            'id_proof_type': pass_obj.get_id_proof_type_display(),
            'id_proof_number': pass_obj.id_proof_number,
            'status': pass_obj.status,
            'status_display': pass_obj.get_status_display(),
            'processed_time': (
                localtime(pass_obj.processed_at).strftime('%Y-%m-%d %H:%M:%S')
                if pass_obj.processed_at else None
            ),
            'processed_by': (
                {'username': pass_obj.processed_by.username}
                if pass_obj.processed_by else None
            ),
        }

    def get_filtered_queryset(self, status):
        qs = Pass.objects.filter(status=status)
        temple = self.request.GET.get('temple')
        date = self.request.GET.get('date')

        if temple:
            qs = qs.filter(temple=temple)
        if date:
            qs = qs.filter(visit_date=date)
        return qs

    def get_pending_passes(self, request):
        self.request = request  # Store request for filtering
        passes = self.get_filtered_queryset('PENDING').order_by('-created_at')
        return JsonResponse([self.get_pass_data(p) for p in passes], safe=False)

    def get_approved_passes(self, request):
        self.request = request
        passes = self.get_filtered_queryset('APPROVED').order_by('-processed_at')
        return JsonResponse([self.get_pass_data(p) for p in passes], safe=False)

    def get_rejected_passes(self, request):
        self.request = request
        passes = self.get_filtered_queryset('REJECTED').order_by('-processed_at')
        return JsonResponse([self.get_pass_data(p) for p in passes], safe=False)

    def can_approve_today(self, pass_obj):
        today = timezone.now().date()
        approved_today = Pass.objects.filter(
            temple=pass_obj.temple,
            status='APPROVED',
            processed_at__date=today
        ).count()
        return approved_today < 1

    def get_pending_passes_for_same_temple_date(self, temple, visit_date):
        """Get all pending passes for the same temple and date"""
        return Pass.objects.filter(
            temple=temple,
            visit_date=visit_date,
            status='PENDING'
        )

    def has_approved_pass_for_temple_date(self, temple, visit_date):
        """Check if there's already an approved pass for this temple and date"""
        return Pass.objects.filter(
            temple=temple,
            visit_date=visit_date,
            status='APPROVED'
        ).exists()

    def can_approve_pass(self, pass_obj):
        """
        Validate if a pass can be approved based on the rules:
        1. Same temple, same date - only if no other pass is approved
        2. Different temple, same date - always allowed
        3. Same temple, different date - always allowed
        """
        # Check if there's already an approved pass for this temple and date
        if self.has_approved_pass_for_temple_date(pass_obj.temple, pass_obj.visit_date):
            return False, "A pass has already been approved for this temple on this date"

        return True, "Pass can be approved"

    def generate_pass_pdf(self, pass_obj):
        """Generate PDF pass from template"""
        try:
            # Format the date for letter number
            letter_date = pass_obj.visit_date.strftime('%d-%m-%Y')
            letter_no = f"Lr. No: {pass_obj.id:03d}/SRISAILAM/{letter_date}"

            # Prepare context for pass template
            context = {
                'letter_no': letter_no,
                'name': pass_obj.name,
                'phone': pass_obj.phone,
                'id_proof_type': pass_obj.get_id_proof_type_display(),
                'id_number': pass_obj.id_proof_number,
                'temple': pass_obj.temple,
                'visit_date': pass_obj.visit_date.strftime('%d-%m-%Y'),
                'num_persons': pass_obj.num_persons,
            }

            # Render the pass template
            html_content = render_to_string('passes/pass_template.html', context)

            # Configure WeasyPrint settings
            from weasyprint import HTML, CSS
            pdf_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)

            # Create PDF with specific page size and margins
            HTML(string=html_content).write_pdf(
                pdf_file.name,
                stylesheets=[
                    CSS(string='''
                        @page {
                            size: A4;
                            margin: 2cm 2cm 2cm 2cm;
                        }
                        @bottom-center {
                        content: element(footer);
                        vertical-align: bottom;
                        }
                    ''')
                ]
            )

            logger.info(f"PDF generated successfully at {pdf_file.name}")
            return pdf_file.name

        except Exception as e:
            logger.error(f"Error generating PDF pass: {str(e)}")
            raise

    def send_notification_email(self, pass_obj, action, additional_message=None):
        """Send email notification with PDF pass attachment for approved passes"""
        pdf_path = None
        try:
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = 'Temple Pass Request ' + action.title()
            msg['From'] = settings.EMAIL_HOST_USER
            msg['To'] = pass_obj.email

            # Prepare context
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

            # Render email template
            template_name = (
                'passes/email_templates/pass_approved.html'
                if action.upper() == 'APPROVED'
                else 'passes/email_templates/pass_rejected.html'
            )
            html_content = render_to_string(template_name, context)
            msg.attach(MIMEText(html_content, 'html'))

            # If approved, generate and attach PDF
            if action.upper() == 'APPROVED':
                try:
                    pdf_path = self.generate_pass_pdf(pass_obj)
                    if pdf_path:
                        with open(pdf_path, 'rb') as pdf_file:
                            pdf_part = MIMEApplication(pdf_file.read(), _subtype='pdf')
                            pdf_part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=f'Temple_Pass_{pass_obj.id}.pdf'
                            )
                            msg.attach(pdf_part)
                except Exception as e:
                    logger.error(f"Error attaching PDF: {str(e)}")
                    raise

            # Send email using SMTP
            try:
                logger.info(f"Attempting to send email to {pass_obj.email}")
                with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                    server.starttls()
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                    server.send_message(msg)
                logger.info(f"Email sent successfully to {pass_obj.email}")
                return True, "Email sent successfully"

            except smtplib.SMTPException as e:
                error_msg = f"SMTP Error: {str(e)}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        finally:
            # Clean up PDF file
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                except Exception as e:
                    logger.warning(f"Could not delete temporary PDF file: {str(e)}")

    def process_pass(self, request, pass_obj, action):
        """Process a pass approval or rejection"""
        if pass_obj.status != 'PENDING':
            return JsonResponse({
                'error': 'This pass is no longer pending'
            }, status=400)

        try:
            # Update the pass status
            pass_obj.status = action.upper()
            pass_obj.processed_at = timezone.now()
            pass_obj.processed_by = request.user
            pass_obj.save()

            # Send email notification
            email_sent, email_message = self.send_notification_email(pass_obj, action)

            # If approved, handle other pending passes
            if action.upper() == 'APPROVED':
                self.reject_other_passes(pass_obj)

            response_data = {
                'status': 'success',
                'message': f'Pass {action.lower()}ed successfully',
                'data': self.get_pass_data(pass_obj),
                'email_status': 'sent' if email_sent else 'failed',
                'email_message': email_message
            }

            if not email_sent:
                logger.error(f"Email sending failed for pass ID {pass_obj.id}: {email_message}")
                response_data['message'] += f' but email notification failed: {email_message}'

            return JsonResponse(response_data)

        except Exception as e:
            error_msg = f"Error processing pass: {str(e)}"
            logger.error(error_msg)
            return JsonResponse({
                'error': error_msg
            }, status=500)

    def reject_other_passes(self, approved_pass):
        """Reject other pending passes for the same temple and date"""
        other_pending_passes = Pass.objects.filter(
            temple=approved_pass.temple,
            visit_date=approved_pass.visit_date,
            status='PENDING'
        ).exclude(id=approved_pass.id)

        for pass_obj in other_pending_passes:
            try:
                pass_obj.status = 'REJECTED'
                pass_obj.processed_at = timezone.now()
                pass_obj.processed_by = approved_pass.processed_by
                pass_obj.save()

                self.send_notification_email(
                    pass_obj,
                    'REJECTED',
                    "Your pass request has been automatically rejected as another pass has been approved for this temple on the same date."
                )
            except Exception as e:
                logger.error(f"Error in rejecting pass ID {pass_obj.id}: {str(e)}")

    def _handle_other_pending_passes(self, approved_pass):
        """Handle other pending passes for the same temple and date"""
        pending_passes = Pass.objects.filter(
            temple=approved_pass.temple,
            visit_date=approved_pass.visit_date,
            status='PENDING'
        ).exclude(id=approved_pass.id)

        for pass_obj in pending_passes:
            try:
                pass_obj.status = 'REJECTED'
                pass_obj.processed_at = timezone.now()
                pass_obj.processed_by = approved_pass.processed_by
                pass_obj.save()

                # Send rejection email
                self.email_service.send_temple_pass_email(pass_obj, 'REJECTED')

            except Exception as e:
                logger.error(f"Error handling pending pass {pass_obj.id}: {str(e)}", exc_info=True)


    def approve_pass(self, request, pass_id):
        try:
            pass_obj = Pass.objects.get(pk=pass_id)
            return self.process_pass(request, pass_obj, 'APPROVED')
        except Pass.DoesNotExist:
            return JsonResponse({
                'error': 'Pass not found'
            }, status=404)

    def reject_pass(self, request, pass_id):
        try:
            pass_obj = Pass.objects.get(pk=pass_id)
            return self.process_pass(request, pass_obj, 'REJECTED')
        except Pass.DoesNotExist:
            return JsonResponse({
                'error': 'Pass not found'
            }, status=404)

    def bulk_reject_passes(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=405)

        try:
            pass_ids = request.POST.getlist('pass_ids[]')
            passes = Pass.objects.filter(id__in=pass_ids, status='PENDING')

            rejected_count = 0
            for pass_obj in passes:
                response = self.process_pass(request, pass_obj, 'REJECTED')
                if response.status_code == 200:
                    rejected_count += 1

            return JsonResponse({
                'status': 'success',
                'message': f'{rejected_count} passes rejected successfully'
            })

        except Exception as e:
            return JsonResponse({
                'error': f'Error rejecting passes: {str(e)}'
            }, status=500)

    def bulk_delete_passes(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Invalid request method'}, status=405)

        try:
            pass_ids = request.POST.getlist('pass_ids[]')
            passes = Pass.objects.filter(
                id__in=pass_ids,
                status__in=['APPROVED', 'REJECTED']
            )
            deleted_count = passes.count()
            passes.delete()

            return JsonResponse({
                'status': 'success',
                'message': f'{deleted_count} passes deleted successfully'
            })

        except Exception as e:
            return JsonResponse({
                'error': f'Error deleting passes: {str(e)}'
            }, status=500)

    def get_pass_counts(self, request):
        filter_params = {}
        if 'temple' in request.GET:
            filter_params['temple'] = request.GET['temple']
        if 'date' in request.GET:
            filter_params['visit_date'] = request.GET['date']

        return JsonResponse({
            'pending': Pass.objects.filter(status='PENDING', **filter_params).count(),
            'approved': Pass.objects.filter(status='APPROVED', **filter_params).count(),
            'rejected': Pass.objects.filter(status='REJECTED', **filter_params).count(),
        })

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    class Media:
        css = {
            'all': ['admin/css/vendor/jquery.min.css']
        }
        js = ['admin/js/vendor/jquery/jquery.min.js']


    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'num_persons':
            field.widget.attrs.update({
                'min': '1',
                'max': '6',
                'title': 'Number of persons must be between 1 and 6'
            })
        return field

