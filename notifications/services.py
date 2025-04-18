import requests
from django.conf import settings
import logging
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)


class EduMarcSMSService:
    BASE_URL = "https://smsapi.edumarcsms.com/api/v1/sendsms"

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_sms(self, recipient, message):
        try:
            # Remove any spaces or special characters from mobile number
            cleaned_recipient = ''.join(filter(str.isdigit, recipient))

            payload = {
                "mobile": cleaned_recipient,
                "message": message,
            }

            # Add timeout to prevent hanging
            response = requests.post(
                self.BASE_URL,
                json=payload,
                headers=self.headers,
                timeout=10  # 10 seconds timeout
            )

            # Log the response for debugging
            logger.debug(f"SMS API Response for {recipient}: {response.status_code} - {response.text}")

            try:
                response_data = response.json()
            except ValueError:
                logger.error(f"Invalid JSON response from SMS API: {response.text}")
                return False, "Invalid response from SMS service"

            # Check for successful response
            # Note: Adjust these conditions based on edumarcsms.com's actual API response format
            if response.status_code == 200:
                return True, None
            else:
                error_message = response_data.get('message', 'Unknown error')
                logger.error(f"SMS API error: {error_message}")
                return False, error_message

        except Timeout:
            logger.error(f"Timeout while sending SMS to {recipient}")
            return False, "Request timed out"

        except RequestException as e:
            logger.error(f"SMS sending failed: {str(e)}")
            return False, f"Failed to send SMS: {str(e)}"

        except Exception as e:
            logger.error(f"Unexpected error while sending SMS: {str(e)}")
            return False, f"Unexpected error: {str(e)}"