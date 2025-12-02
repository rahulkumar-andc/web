import os
import django
from django.core.exceptions import ValidationError

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.forms import CustomUserCreationForm

def test_username_validation():
    print("Testing username validation...")
    
    # Test cases: (username, should_pass)
    test_cases = [
        ("valid_user_1", True),
        ("User123", True),
        ("user.name", False),  # Current: True, Desired: False
        ("user@name", False),  # Current: True, Desired: False
        ("user-name", False),  # Current: True, Desired: False
        ("user+name", False),  # Current: True, Desired: False
        ("invalid space", False),
        ("short", True), # "short" is 5 chars, > 3. Wait, min length is 3.
        ("ab", False),
    ]

    form = CustomUserCreationForm()
    
    for username, should_pass in test_cases:
        form.cleaned_data = {'username': username}
        try:
            form.clean_username()
            if not should_pass:
                print(f"FAIL: Username '{username}' passed validation but should have failed.")
            else:
                print(f"PASS: Username '{username}' passed validation as expected.")
        except ValidationError as e:
            if should_pass:
                print(f"FAIL: Username '{username}' failed validation with error: {e}")
            else:
                print(f"PASS: Username '{username}' failed validation as expected.")

if __name__ == "__main__":
    test_username_validation()
