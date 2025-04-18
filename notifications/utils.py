import requests
from django.conf import settings
from .models import NotificationLog
import datetime
import json
import logging
import re

logger = logging.getLogger(__name__)


class EduMarcSMSService:
    def __init__(self):
        self.api_url = settings.EDUMARC_API_URL or 'https://smsapi.edumarcsms.com/api/v1/sendsms'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.EDUMARC_API_KEY}'  # Changed to Bearer token
        }

    def format_mobile_number(self, number):
        """Format mobile number to required format."""
        # Remove any non-digit characters
        number = re.sub(r'\D', '', number)

        # If number starts with '91', remove it
        if number.startswith('91') and len(number) > 10:
            number = number[2:]

        # If number starts with '0', remove it
        if number.startswith('0'):
            number = number[1:]

        # Ensure the number is 10 digits
        if len(number) != 10:
            raise ValueError(f"Invalid mobile number length: {len(number)}")

        return number

    def send_sms(self, recipient, message, template_id=None):
        try:
            # Format the mobile number
            formatted_number = self.format_mobile_number(recipient)

            # Prepare the payload according to Edumarc API documentation
            payload = {
                "message": message,
                "sender": settings.EDUMARC_SENDER_ID,  # Changed from senderId to sender
                "mobile": formatted_number,  # Changed from number array to single mobile
                "templateId": template_id,
                "route": "4",  # Add route parameter
                "msgType": "text"  # Add message type
            }

            # Log the request for debugging
            logger.info(f"Sending SMS to {formatted_number}")
            logger.debug(f"Request payload: {json.dumps(payload)}")
            logger.debug(f"Headers: {json.dumps(self.headers)}")

            # Make the API request
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            # Log the complete response
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response content: {response.text}")

            try:
                response_data = response.json()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {response.text}")
                return False, "Invalid response from server"

            # Check for successful response
            if response.status_code == 200:
                if response_data.get('status') in ['success', True, 'true', 1]:
                    logger.info(f"SMS sent successfully to {formatted_number}")
                    return True, None
                else:
                    error_msg = response_data.get('message') or 'Unknown API error'
                    logger.error(f"API Error: {error_msg}")
                    return False, error_msg
            else:
                error_msg = f"HTTP {response.status_code}: {response_data.get('message', 'Unknown error')}"
                logger.error(error_msg)
                return False, error_msg

        except ValueError as e:
            error_msg = f"Invalid mobile number: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


class NotificationSender:
    def __init__(self):
        self.sms_service = EduMarcSMSService()

    def send_notification(self, notification_log):
        try:
            success = False
            error_message = None

            if notification_log.channel in ['SMS', 'BOTH']:
                # Get template details
                template = notification_log.template
                if not template:
                    raise ValueError("No template associated with notification")

                template_id = template.template_id
                if not template_id:
                    raise ValueError("Template ID not found")

                # Process message content with template variables if any
                message = template.content

                # Send SMS
                sms_success, sms_error = self.sms_service.send_sms(
                    notification_log.recipient,
                    message,
                    template_id
                )

                if sms_success:
                    success = True
                else:
                    error_message = sms_error

            # Update notification log
            notification_log.status = NotificationLog.Status.SENT if success else NotificationLog.Status.FAILED
            notification_log.error_message = error_message or ''
            notification_log.sent_at = datetime.datetime.now() if success else None
            notification_log.save()

            return success, error_message

        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in send_notification: {error_message}")

            # Update notification log with error
            notification_log.status = NotificationLog.Status.FAILED
            notification_log.error_message = error_message
            notification_log.save()

            return False, error_message