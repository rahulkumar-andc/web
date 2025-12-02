
import os
import django
from django.test import Client, RequestFactory
from django.test.utils import setup_test_environment

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.models import CustomUser, Note
from tools.models import Tool

def verify_profile():
    print("Verifying Profile Page Enhancement...")
    setup_test_environment()
    
    # Create a test user
    username = 'profile_test_user'
    email = 'profile_test@example.com'
    password = 'testpassword123'
    
    try:
        user = CustomUser.objects.get(username=username)
        user.delete()
        print(f"Deleted existing user {username}")
    except CustomUser.DoesNotExist:
        pass
        
    user = CustomUser.objects.create_user(username=username, email=email, password=password)
    print(f"Created user {username}")
    
    # Create dummy tools
    tool1, _ = Tool.objects.get_or_create(title="Test Tool 1", slug="test-tool-1", category="Web")
    tool2, _ = Tool.objects.get_or_create(title="Test Tool 2", slug="test-tool-2", category="Security")
    
    # Create dummy notes
    note1, _ = Note.objects.get_or_create(title="Test Note 1", slug="test-note-1", category="python", author=user, file="dummy.pdf")
    
    # Add to purchased
    user.purchased_tools.add(tool1, tool2)
    user.purchased_notes.add(note1)
    user.save()
    print("Added tools and notes to user's purchased list")
    
    # Test Profile View
    client = Client()
    client.force_login(user)
    
    response = client.get('/profile/')
    
    if response.status_code == 200:
        print("Profile page loaded successfully (200 OK)")
        content = response.content.decode('utf-8')
        
        # Check for Tabs
        if 'onclick="openTab(event, \'info\')"' in content:
            print("PASS: Info tab found")
        else:
            print("FAIL: Info tab missing")
            
        if 'onclick="openTab(event, \'tools\')"' in content:
            print("PASS: Tools tab found")
        else:
            print("FAIL: Tools tab missing")
            
        if 'onclick="openTab(event, \'notes\')"' in content:
            print("PASS: Notes tab found")
        else:
            print("FAIL: Notes tab missing")
            
        # Check for Content
        if "Test Tool 1" in content and "Test Tool 2" in content:
            print("PASS: Purchased tools displayed")
        else:
            print("FAIL: Purchased tools NOT displayed")
            
        if "Test Note 1" in content:
            print("PASS: Purchased notes displayed")
        else:
            print("FAIL: Purchased notes NOT displayed")
            
        # Check for Cyberpunk classes
        if "profile-container" in content and "items-grid" in content:
            print("PASS: Cyberpunk styles applied")
        else:
            print("FAIL: Cyberpunk styles missing")
            
    else:
        print(f"FAIL: Profile page failed to load. Status: {response.status_code}")

if __name__ == '__main__':
    verify_profile()
