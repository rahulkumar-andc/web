from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_email_task(self, subject, message, recipient_list, from_email=None, **kwargs):
    """
    Async task to send email with retry logic.
    Retries 3 times with delays: 5s, 10s, 20s.
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
        
    try:
        logger.info(f"Sending email to {recipient_list}: {subject}")
        send_mail(subject, message, from_email, recipient_list, **kwargs)
        logger.info(f"Email sent successfully to {recipient_list}")
    except Exception as exc:
        logger.error(f"Email sending failed: {exc}. Retrying...")
        
        # Exponential backoff: 5 * 2^retries
        # Retry 0: 5 * 1 = 5s
        # Retry 1: 5 * 2 = 10s
        # Retry 2: 5 * 4 = 20s
        delay = 5 * (2 ** self.request.retries)
        
        raise self.retry(exc=exc, countdown=delay)
