import os
import django
import json
from django.test import RequestFactory
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.views import csp_report
from core.models import SecurityLog

def verify_csp():
    print("Verifying CSP Reporter Endpoint...")
    
    factory = RequestFactory()
    
    # Sample CSP Report Payload
    payload = {
        "csp-report": {
            "document-uri": "http://example.com/signup.html",
            "referrer": "",
            "blocked-uri": "http://evil.com/style.css",
            "violated-directive": "style-src cdn.example.com",
            "original-policy": "default-src 'none'; style-src cdn.example.com; report-uri /_/csp-reports"
        }
    }
    
    request = factory.post(
        '/core/csp-report/',
        data=json.dumps(payload),
        content_type='application/json'
    )
    
    # Attach user to request (RequestFactory doesn't do this via middleware)
    from django.contrib.auth.models import AnonymousUser
    request.user = AnonymousUser()
    
    # Call the view
    response = csp_report(request)
    
    print(f"Response Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("Response OK -> PASS")
        
        # Check if log was created
        log = SecurityLog.objects.filter(action='csp_violation').last()
        if log:
            print("SecurityLog created -> PASS")
            print(f"Log Details: {log.details}")
            if log.details.get('blocked-uri') == "http://evil.com/style.css":
                print("Log content correct -> PASS")
            else:
                print("Log content incorrect -> FAIL")
        else:
            print("SecurityLog NOT created -> FAIL")
    else:
        print("Response NOT OK -> FAIL")

if __name__ == '__main__':
    verify_csp()
