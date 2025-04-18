from django.http import JsonResponse
from django.utils import timezone
import json
from django.views.decorators.http import require_http_methods
from .models import NotificationTemplate, NotificationLog
from .utils import NotificationSender
from voters.models import Voter
import requests



@require_http_methods(["GET"])
def get_templates(request, type_id):
    """Get templates for a specific notification type"""
    templates = NotificationTemplate.objects.filter(
        notification_type_id=type_id
    ).values('id', 'name', 'template_id')  # Add template_id to the values
    return JsonResponse({'templates': list(templates)})


@require_http_methods(["POST"])
def send_notifications(request):
    """Send notifications to selected voters"""
    try:
        data = json.loads(request.body)
        template_id = data.get('template_id')
        channel = data.get('channel')
        voter_ids = data.get('recipients', [])

        if not all([template_id, channel, voter_ids]):
            return JsonResponse({
                'success': False,
                'error': 'Missing required parameters'
            })

        template = NotificationTemplate.objects.get(id=template_id)

        # Get voters with their mobile numbers
        voters = Voter.objects.filter(id__in=voter_ids)

        # If channel is SMS, send using Edumarc SMS API
        if channel.lower() == 'sms':
            sms_api_url = 'https://smsapi.edumarcsms.com/api/v1/sendsms'
            headers = {
                'Content-Type': 'application/json',
                'apikey': 'clnnab4k2000bj7qx6h14fu7r'  # Your API key
            }

            # Collect all mobile numbers
            mobile_numbers = []
            for voter in voters:
                # Assuming mobile number is stored in voter.data['MOBILE']
                mobile_number = voter.data.get('MOBILE')
                if mobile_number:
                    mobile_numbers.append(str(mobile_number))

            if not mobile_numbers:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid mobile numbers found'
                })

            # Prepare SMS request payload
            sms_data = {
                "message": template.content,
                "senderId": "EDUMRC",  # Your sender ID
                "number": mobile_numbers,
                "templateId": template.template_id  # DLT approved template ID
            }

            # Send SMS using Edumarc API
            response = requests.post(
                sms_api_url,
                headers=headers,
                json=sms_data
            )

            api_response = response.json()

            # Create notification logs
            logs = []
            for voter in voters:
                status = NotificationLog.Status.SENT if response.status_code == 200 else NotificationLog.Status.FAILED
                logs.append(NotificationLog(
                    recipient=voter.id,
                    template=template,
                    channel=channel,
                    status=status,
                    sent_at=timezone.now() if status == NotificationLog.Status.SENT else None,
                    response_data=api_response
                ))

            # Bulk create logs
            NotificationLog.objects.bulk_create(logs)

            if response.status_code != 200:
                return JsonResponse({
                    'success': False,
                    'error': f'SMS API Error: {api_response}'
                })

            return JsonResponse({
                'success': True,
                'message': 'SMS sent successfully',
                'api_response': api_response
            })

        # Handle other channels here if needed

        return JsonResponse({'success': True})

    except NotificationTemplate.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Template not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })