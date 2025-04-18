from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.db.models import Q
from .models import Pass


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

    def process_pass(self, request, pass_obj, action):
        if pass_obj.status != 'PENDING':
            return JsonResponse({
                'error': 'This pass is no longer pending'
            }, status=400)

        if action.upper() == 'APPROVED' and not self.can_approve_today(pass_obj):
            return JsonResponse({
                'error': 'Maximum number of approvals for today has been reached'
            }, status=400)

        try:
            pass_obj.status = action.upper()
            pass_obj.processed_at = timezone.now()
            pass_obj.processed_by = request.user
            pass_obj.save()

            # Send email notification
            context = {
                'name': pass_obj.name,
                'temple': pass_obj.temple,
                'visit_date': pass_obj.visit_date.strftime('%Y-%m-%d'),
                'num_persons': pass_obj.num_persons,
                'id_proof_type': pass_obj.get_id_proof_type_display(),
                'id_proof_number': pass_obj.id_proof_number,
                'status': action.upper(),
                'processed_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'processed_by': request.user.username,
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

            try:
                html_message = render_to_string(template_name, context)
                send_mail(
                    subject=subject,
                    message='',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[pass_obj.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email Error: {str(e)}")

            return JsonResponse({
                'status': 'success',
                'message': f'Pass {action.lower()}ed successfully',
                'data': self.get_pass_data(pass_obj)
            })

        except Exception as e:
            return JsonResponse({
                'error': f'Error processing pass: {str(e)}'
            }, status=500)

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

