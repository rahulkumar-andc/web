import os
import django
from django.test import RequestFactory, Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.models import CustomUser
from custom_admin.views import dashboard, analytics_api

def verify_dashboard_ui():
    print("Verifying Dashboard UI Polish...")
    
    # 1. Setup Admin User
    user, created = CustomUser.objects.get_or_create(username='ui_admin', email='ui@example.com')
    if created:
        user.set_password('password')
        user.is_superuser = True
        user.is_staff = True
        user.save()
        
    # 2. Test API Endpoint
    print("\nTest 1: Analytics API...")
    factory = RequestFactory()
    request = factory.get('/custom_admin/api/analytics/')
    request.user = user
    
    response = analytics_api(request)
    if response.status_code == 200:
        print("API Status 200 -> PASS")
        import json
        data = json.loads(response.content)
        if 'dau_count' in data and 'failed_logins_chart' in data:
            print("API Data Structure -> PASS")
        else:
            print("API Data Structure -> FAIL")
    else:
        print(f"API Failed (Status: {response.status_code}) -> FAIL")
        
    # 3. Test Dashboard Rendering (Template Check)
    print("\nTest 2: Dashboard Template...")
    client = Client()
    client.force_login(user)
    # Note: We need the actual URL, assuming it's hooked up in custom_admin/urls.py
    # But since we can't easily check URL resolving without the full URL conf loaded in a specific way,
    # let's just call the view directly with a request that has a user.
    
    request = factory.get('/custom_admin/dashboard/')
    request.user = user
    response = dashboard(request)
    
    if response.status_code == 200:
        print("Dashboard Render 200 -> PASS")
        content = response.content.decode('utf-8')
        if 'cyberpunk.css' in content:
            print("Cyberpunk CSS Linked -> PASS")
        else:
            print("Cyberpunk CSS Missing -> FAIL")
            
        if 'failedLoginsChart' in content:
            print("Chart.js Config Present -> PASS")
        else:
            print("Chart.js Config Missing -> FAIL")
    else:
        print(f"Dashboard Render Failed (Status: {response.status_code}) -> FAIL")

if __name__ == '__main__':
    verify_dashboard_ui()
