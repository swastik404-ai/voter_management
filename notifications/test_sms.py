import os
import sys
import django
import logging
from datetime import datetime

# Add the project root directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voter_management.settings')
django.setup()

from notifications.utils import EduMarcSMSService
from notifications.models import NotificationTemplate, NotificationLog
from voters.models import Voter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(current_dir, 'sms_test.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def test_sms_sending():
    try:
        logger.info("Starting SMS test...")
        logger.info(f"Current directory: {os.getcwd()}")
        logger.info(f"Project root: {project_root}")

        # Initialize SMS service
        sms_service = EduMarcSMSService()

        # Test mobile number (replace with a valid number)
        test_mobile = "7905285898"  # Replace with actual test number

        # Test message
        test_message = "This is a test SMS message."

        # Get first available template from database
        template = NotificationTemplate.objects.first()
        if not template:
            logger.error("No notification templates found in database")
            return False, "No templates available"

        template_id = template.template_id
        logger.info(f"Using template: {template.name} (ID: {template_id})")

        # Attempt to send SMS
        logger.info(f"Sending test SMS to {test_mobile}")
        success, error = sms_service.send_sms(
            recipient=test_mobile,
            message=test_message,
            template_id=template_id
        )

        if success:
            logger.info("✓ SMS sent successfully!")
        else:
            logger.error(f"✗ SMS sending failed: {error}")

        return success, error

    except Exception as e:
        logger.exception("Test failed with error")
        return False, str(e)


def test_with_real_voter():
    try:
        # Get first voter with a mobile number
        voter = Voter.objects.filter(mobile_no__isnull=False).first()
        if not voter:
            logger.error("No voters found with mobile numbers")
            return False, "No voters available"

        logger.info(f"Testing with voter: {voter.mobile_no}")

        # Get first template
        template = NotificationTemplate.objects.first()
        if not template:
            logger.error("No templates found")
            return False, "No templates available"

        logger.info(f"Using template: {template.name}")

        # Create notification log
        notification_log = NotificationLog.objects.create(
            recipient=voter.mobile_no,
            template=template,
            channel='SMS',
            status='PENDING'
        )

        # Initialize SMS service
        sms_service = EduMarcSMSService()

        # Send SMS
        success, error = sms_service.send_sms(
            recipient=voter.mobile_no,
            message=template.content,
            template_id=template.template_id
        )

        # Update notification log
        notification_log.status = 'SENT' if success else 'FAILED'
        notification_log.error_message = error if error else ''
        notification_log.sent_at = datetime.now() if success else None
        notification_log.save()

        if success:
            logger.info("✓ SMS sent successfully to real voter!")
        else:
            logger.error(f"✗ SMS sending failed: {error}")

        return success, error

    except Exception as e:
        logger.exception("Test with real voter failed")
        return False, str(e)


def verify_settings():
    """Verify that all required settings are available"""
    from django.conf import settings

    required_settings = [
        'EDUMARC_API_KEY',
        'EDUMARC_SENDER_ID',
        'EDUMARC_API_URL'
    ]

    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)

    if missing_settings:
        logger.error(f"Missing required settings: {', '.join(missing_settings)}")
        return False

    logger.info("All required settings are configured")
    return True


if __name__ == "__main__":
    print("\nStarting SMS Testing Suite")
    print("=" * 50)

    # First verify settings
    if not verify_settings():
        print("❌ Settings verification failed. Please check your settings.py")
        sys.exit(1)

    # Run test with test number
    print("\n1. Testing with test number:")
    success1, error1 = test_sms_sending()
    print(f"Result: {'✓ Success' if success1 else '✗ Failed'}")
    if error1:
        print(f"Error: {error1}")

    # Run test with real voter
    print("\n2. Testing with real voter:")
    success2, error2 = test_with_real_voter()
    print(f"Result: {'✓ Success' if success2 else '✗ Failed'}")
    if error2:
        print(f"Error: {error2}")

    print("\nCheck sms_test.log for detailed information")