import os
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.template import Context, Template

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

def verify_template():
    print("Verifying base.html template...")
    try:
        # We need a request object for some tags like 'url' or 'static' if they depend on context processors
        # But render_to_string might work if we mock the context
        from django.test import RequestFactory
        factory = RequestFactory()
        request = factory.get('/')
        request.user = django.contrib.auth.models.AnonymousUser()
        
        # Render the template
        rendered = render_to_string('core/base.html', request=request)
        print("Template rendered successfully!")
    except Exception as e:
        print(f"Template rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_template()
