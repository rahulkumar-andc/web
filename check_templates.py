import os
import django
from django.conf import settings
from django.template import Template, Context, Engine
from django.template.loader import get_template

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

def check_templates():
    template_dirs = [
        'core/templates',
        'tools/templates',
        'custom_admin/templates',
    ]
    
    errors = []
    
    for root_dir in template_dirs:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.endswith('.html'):
                    filepath = os.path.join(dirpath, filename)
                    try:
                        # Try to load the template
                        # We use get_template to simulate actual loading which includes inheritance checks
                        # However, get_template requires the relative path from template dirs
                        
                        # Calculate relative path
                        rel_path = os.path.relpath(filepath, root_dir)
                        # Fix for nested template dirs if any, but standard django setup usually has 'app/templates/app/...'
                        # Actually, get_template expects the path as used in {% include %} or render()
                        # If our structure is standard app/templates/..., then the path is relative to app/templates/
                        
                        # Let's try to just read and parse the file content directly first to catch syntax errors
                        # This avoids issues with finding the correct relative path for get_template if configuration is complex
                        
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Create a Template object from the string
                        # This will parse the template and raise TemplateSyntaxError if syntax is invalid
                        Template(content)
                        
                        print(f"OK: {filepath}")
                        
                    except Exception as e:
                        if 'base.html' in filepath:
                             print(f"DEBUG CONTENT for {filepath}:")
                             print(content[:500])
                        print(f"ERROR: {filepath} - {e}")
                        errors.append((filepath, str(e)))

    print("\n" + "="*50)
    print(f"Found {len(errors)} errors.")
    for path, error in errors:
        print(f"File: {path}\nError: {error}\n")

if __name__ == '__main__':
    check_templates()
