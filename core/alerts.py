import logging
from django.conf import settings
from .tasks import send_email_task

logger = logging.getLogger(__name__)

def send_security_email(user, subject, message, details=None):
    """
    Send a security alert email to the user.
    """
    if not user.email:
        logger.warning(f"Cannot send security email to {user.username}: No email address")
        return

    try:
        full_message = f"Hello {user.username},\n\n{message}\n\n"
        
        if details:
            full_message += "Details:\n"
            for k, v in details.items():
                full_message += f"- {k}: {v}\n"
        
        full_message += "\nIf this wasn't you, please secure your account immediately.\n\nRegards,\nVillenSec Security Team"
        
        # Async call
        send_email_task.delay(
            subject=f"[VillenSec Security] {subject}",
            message=full_message,
            recipient_list=[user.email]
        )
        logger.info(f"Security email queued for {user.username}: {subject}")
        
        # Also trigger SMS if phone number exists
        if user.phone_number:
            send_sms_alert(user, f"Security Alert: {subject}")
            
    except Exception as e:
        logger.error(f"Failed to queue security email for {user.username}: {e}")

def send_admin_alert(subject, message, details=None):
    """
    Send an immediate alert to admins.
    """
    try:
        # Get admin emails
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admins = User.objects.filter(is_superuser=True).exclude(email='')
        admin_emails = [admin.email for admin in admins]
        
        if not admin_emails:
            logger.warning("No admin emails found for alerts")
            return

        full_message = f"ADMIN ALERT: {message}\n\n"
        if details:
            full_message += "Details:\n"
            for k, v in details.items():
                full_message += f"- {k}: {v}\n"

        # Async call
        send_email_task.delay(
            subject=f"[VillenSec ADMIN] {subject}",
            message=full_message,
            recipient_list=admin_emails
        )
        logger.info(f"Admin alert queued: {subject}")
        
    except Exception as e:
        logger.error(f"Failed to queue admin alert: {e}")

def send_sms_alert(user, message):
    """
    Mock SMS alert. Logs to console.
    """
    if not user.phone_number:
        return
        
    # Mock implementation
    logger.info(f"MOCK SMS to {user.phone_number}: {message}")
    print(f"--- SMS ALERT to {user.phone_number} ---\n{message}\n--------------------------------")
