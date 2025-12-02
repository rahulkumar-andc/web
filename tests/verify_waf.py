import os
import django
from django.conf import settings
from django.test import RequestFactory
from django.http import HttpResponse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.middleware import WAFMiddleware
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch

def verify_waf():
    print("Verifying WAF Implementation...")
    
    # Mock the Celery task to avoid Redis connection errors
    with patch('core.tasks.send_email_task.delay') as mock_task:
        factory = RequestFactory()
        get_response = lambda request: HttpResponse("OK")
        middleware = WAFMiddleware(get_response)
        
        def get_request(url):
            request = factory.get(url)
            request.user = AnonymousUser()
            return request
        
        # Indent the rest of the function or just use the mock globally?
        # Easier to just patch it for the whole execution
        pass
        
    # Actually, let's just patch it at the module level or inside the loop?
    # Since the middleware imports it, we need to patch where it is used.
    # Middleware calls: send_admin_alert.delay(...)
    # It imports send_admin_alert from core.tasks
    
    # Let's wrap the whole logic in the patch context
    with patch('core.tasks.send_email_task.delay'):
        _run_tests(factory, middleware, get_request)

def _run_tests(factory, middleware, get_request):
    # 1. Test SQL Injection
    print("\n1. Testing SQL Injection...")
    sqli_payloads = [
        "/search?q=' OR 1=1 --",
        "/search?q=UNION SELECT 1,2,3",
        "/login?username=admin'--",
    ]
    
    for url in sqli_payloads:
        request = get_request(url)
        response = middleware(request)
        if response.status_code == 403:
            print(f"Blocked SQLi: {url} -> PASS")
        else:
            print(f"Failed to block SQLi: {url} -> FAIL (Status: {response.status_code})")

    # 2. Test XSS
    print("\n2. Testing XSS...")
    xss_payloads = [
        "/comment?text=<script>alert(1)</script>",
        "/profile?bio=<img src=x onerror=alert(1)>",
        "/search?q=javascript:alert(1)",
    ]
    
    for url in xss_payloads:
        request = get_request(url)
        response = middleware(request)
        if response.status_code == 403:
            print(f"Blocked XSS: {url} -> PASS")
        else:
            print(f"Failed to block XSS: {url} -> FAIL (Status: {response.status_code})")
            
    # 3. Test Honeypot
    print("\n3. Testing Honeypot...")
    honeypots = [
        "/wp-admin/",
        "/phpmyadmin/",
        "/.env",
    ]
    
    for url in honeypots:
        request = get_request(url)
        response = middleware(request)
        if response.status_code == 403:
            print(f"Blocked Honeypot: {url} -> PASS")
        else:
            print(f"Failed to block Honeypot: {url} -> FAIL (Status: {response.status_code})")
            
    # 4. Test Legitimate Request
    print("\n4. Testing Legitimate Request...")
    request = get_request("/search?q=hello world")
    response = middleware(request)
    if response.status_code == 200:
        print("Allowed Legitimate Request -> PASS")
    else:
        print(f"Blocked Legitimate Request -> FAIL (Status: {response.status_code})")

    print("\nWAF Verification Completed!")

if __name__ == '__main__':
    verify_waf()
