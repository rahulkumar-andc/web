import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from custom_admin.views import dashboard
from core.models import CustomUser
from django.test.utils import setup_test_environment

setup_test_environment()

def verify_analytics():
    print("Verifying Analytics Dashboard...")
    
    # Create a superuser for testing
    user, created = CustomUser.objects.get_or_create(username='analytics_admin', email='admin@example.com')
    if created:
        user.set_password('password')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        
    factory = RequestFactory()
    request = factory.get('/panel/')
    request.user = user
    
    response = dashboard(request)
    
    if response.status_code == 200:
        print("Dashboard loaded successfully -> PASS")
        
        # Check Context Data
        # Note: In a real view call, context is not directly accessible on HttpResponse unless using Client
        # But since we are calling the view function directly, it returns HttpResponse (from render)
        # We can't easily check context without using Client or mocking render
        
        # Let's use Client instead
        from django.test import Client
        client = Client()
        client.force_login(user)
        response = client.get('/panel/')
        
        context = response.context
        
        required_keys = [
            'dau_count',
            'total_downloads',
            'popular_tools',
            'estimated_revenue',
            'failed_logins_chart',
            'map_ips'
        ]
        
        all_present = True
        for key in required_keys:
            if key in context:
                print(f"Context key '{key}' present -> PASS")
            else:
                print(f"Context key '{key}' MISSING -> FAIL")
                all_present = False
                
        if all_present:
            print("\nAll analytics metrics present in context!")
        else:
            print("\nSome metrics are missing.")
            
    else:
        print(f"Dashboard failed to load (Status: {response.status_code}) -> FAIL")

if __name__ == '__main__':
    verify_analytics()
