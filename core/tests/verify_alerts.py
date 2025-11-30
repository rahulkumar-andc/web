import os
import django
from unittest.mock import patch, MagicMock

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.alerts import send_security_email, send_admin_alert
from core.models import CustomUser

def verify_alerts():
    print("Verifying Security Alerts...")
    
    # Create test user
    user, _ = CustomUser.objects.get_or_create(username='alert_test_user', email='test@example.com')
    user.phone_number = '+1234567890'
    user.save()
    
    # Mock send_email_task.delay
    with patch('core.tasks.send_email_task.delay') as mock_task:
        # Test 1: Security Email
        print("\nTest 1: Sending Security Email...")
        send_security_email(
            user, 
            "Test Alert", 
            "This is a test alert.", 
            details={'IP': '1.2.3.4'}
        )
        
        if mock_task.called:
            print("send_email_task.delay called -> PASS")
            args, kwargs = mock_task.call_args
            # kwargs might be in args or kwargs depending on how delay is called
            # delay(subject=..., message=..., recipient_list=...)
            # kwargs are passed as named arguments to delay
            
            # Check arguments
            call_kwargs = mock_task.call_args.kwargs
            if not call_kwargs and mock_task.call_args.args:
                 # It might be called with args if signature matches, but we used keyword args in alerts.py
                 pass
            
            if 'recipient_list' in call_kwargs:
                recipients = call_kwargs['recipient_list']
                if 'test@example.com' in recipients:
                    print("Recipient correct -> PASS")
                else:
                    print(f"Recipient incorrect: {recipients} -> FAIL")
            else:
                 print("recipient_list not found in kwargs -> WARNING (might be positional)")

        else:
            print("send_email_task.delay NOT called -> FAIL")
            
        # Test 2: Admin Alert
        print("\nTest 2: Sending Admin Alert...")
        mock_task.reset_mock()
        
        # Ensure there is an admin
        admin, _ = CustomUser.objects.get_or_create(username='admin_alert_test', email='admin@example.com')
        admin.is_superuser = True
        admin.save()
        
        send_admin_alert("Test Admin Alert", "Something bad happened.")
        
        if mock_task.called:
            print("send_email_task.delay called -> PASS")
            call_kwargs = mock_task.call_args.kwargs
            if 'recipient_list' in call_kwargs:
                recipients = call_kwargs['recipient_list']
                if 'admin@example.com' in recipients:
                    print("Recipient correct -> PASS")
                else:
                    print(f"Recipient incorrect: {recipients} -> FAIL")
            else:
                 print("recipient_list not found in kwargs -> WARNING")
        else:
            print("send_email_task.delay NOT called -> FAIL")

if __name__ == '__main__':
    verify_alerts()
