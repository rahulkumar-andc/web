import os
import django
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

# Enable eager execution for testing
from django.conf import settings
settings.CELERY_TASK_ALWAYS_EAGER = True

from core.tasks import send_email_task

def verify_tasks():
    print("Verifying Async Tasks...")
    
    # Test 1: Successful Email
    print("\nTest 1: Successful Email Task...")
    with patch('core.tasks.send_mail') as mock_send_mail:
        send_email_task.delay(
            "Test Subject",
            "Test Message",
            ['test@example.com']
        )
        
        if mock_send_mail.called:
            print("send_mail called -> PASS")
        else:
            print("send_mail NOT called -> FAIL")
            
    # Test 2: Retry Logic
    print("\nTest 2: Retry Logic (Simulation)...")
    # Note: Testing actual retries with Eager mode is tricky because it raises the exception immediately.
    # We will verify the task is configured correctly.
    
    print(f"Max Retries: {send_email_task.max_retries}")
    if send_email_task.max_retries == 3:
        print("Max Retries = 3 -> PASS")
    else:
        print(f"Max Retries = {send_email_task.max_retries} -> FAIL")
        
    # We can try to manually call the task and force an exception to see if it tries to retry
    with patch('core.tasks.send_mail', side_effect=Exception("SMTP Error")) as mock_fail:
        try:
            # We need to mock self.retry to avoid actual retry scheduling in eager mode which might fail or loop
            with patch.object(send_email_task, 'retry', side_effect=Retry) as mock_retry:
                try:
                    send_email_task(
                        "Test Subject",
                        "Test Message",
                        ['test@example.com']
                    )
                except Retry:
                    print("Task raised Retry exception -> PASS")
                    
                    # Check countdown
                    if mock_retry.called:
                        kwargs = mock_retry.call_args[1]
                        countdown = kwargs.get('countdown')
                        print(f"Retry Countdown: {countdown}")
                        # First retry should be 5 * 2^0 = 5
                        if countdown == 5:
                            print("Countdown correct (5s) -> PASS")
                        else:
                            print(f"Countdown incorrect: {countdown} -> FAIL")
                    else:
                        print("Retry not called -> FAIL")
                        
        except Exception as e:
            print(f"Unexpected exception: {e}")

if __name__ == '__main__':
    verify_tasks()
