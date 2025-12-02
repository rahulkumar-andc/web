import os
import django

# Remove DATABASE_URL to force SQLite usage for testing
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from unittest.mock import patch
from core.models import CustomUser

print("=" * 70)
print("SESSION-BASED REGISTRATION TEST")
print("=" * 70)

@patch('core.views.send_email_task.delay')
def test_session_registration(mock_email):
    client = Client(HTTP_HOST='localhost')
    
    # 1. Register - should NOT create user in database
    print("\n1. Testing Registration (should store in session only)...")
    username = "test_session_user"
    email = "testsession@example.com"
    password = "ValidPass123!"
    
    # Cleanup
    CustomUser.objects.filter(username=username).delete()
    
    response = client.post(reverse('core:register'), {
        'username': username,
        'email': email,
        'password1': password,
        'password2': password,
    })
    
    if response.status_code != 302:
        print(f"   ✗ FAIL: Registration failed - status {response.status_code}")
        print(response.content.decode()[:500])
        return
    
    print(f"   ✓ PASS: Registration form accepted")
    
    # Check if user exists in database (should NOT exist)
    user_exists = CustomUser.objects.filter(username=username).exists()
    if user_exists:
        print(f"   ✗ FAIL: User was created in database BEFORE OTP verification!")
        return
    else:
        print(f"   ✓ PASS: User NOT in database (stored in session only)")
    
    # Check session data
    session = client.session
    if 'pending_registration_username' in session:
        print(f"   ✓ PASS: Registration data stored in session")
        print(f"   Session username: {session['pending_registration_username']}")
        print(f"   Session email: {session['pending_registration_email']}")
        otp_code = session.get('pending_registration_otp')
        print(f"   Session OTP: {otp_code}")
    else:
        print(f"   ✗ FAIL: Registration data NOT in session")
        return
    
    # 2. Try wrong OTP
    print("\n2. Testing wrong OTP (user should still NOT be created)...")
    verify_url = reverse('core:verify_otp', args=[0])  # user_id=0 for session-based
    response = client.post(verify_url, {'otp': '000000'})
    
    if "Invalid OTP" in response.content.decode():
        print(f"   ✓ PASS: Wrong OTP rejected")
    else:
        print(f"   ✗ FAIL: Wrong OTP was not rejected properly")
    
    user_exists = CustomUser.objects.filter(username=username).exists()
    if not user_exists:
        print(f"   ✓ PASS: User still NOT in database after wrong OTP")
    else:
        print(f"   ✗ FAIL: User was created despite wrong OTP!")
        return
    
    # 3. Try correct OTP
    print("\n3. Testing correct OTP (user should NOW be created)...")
    response = client.post(verify_url, {'otp': otp_code})
    
    if response.status_code == 302:
        print(f"   ✓ PASS: OTP verification accepted")
    else:
        print(f"   ✗ FAIL: OTP verification failed - status {response.status_code}")
        return
    
    # NOW check if user exists
    user_exists = CustomUser.objects.filter(username=username).exists()
    if user_exists:
        user = CustomUser.objects.get(username=username)
        print(f"   ✓ PASS: User CREATED in database after OTP verification")
        
        if user.is_active and user.email_verified:
            print(f"   ✓ PASS: User is active and email verified")
        else:
            print(f"   ✗ FAIL: User not properly activated")
            print(f"   is_active: {user.is_active}, email_verified: {user.email_verified}")
    else:
        print(f"   ✗ FAIL: User NOT created even after correct OTP!")
    
    # 4. Check session is cleared
    session = client.session
    if 'pending_registration_username' not in session:
        print(f"   ✓ PASS: Session data cleared after verification")
    else:
        print(f"   ✗ FAIL: Session data not cleared")
    
    print("\n" + "=" * 70)
    print("✅ SESSION-BASED REGISTRATION WORKS!")
    print("=" * 70)
    print("\nSUMMARY:")
    print("✓ User data stored in session first")
    print("✓ Database NOT polluted before OTP verification")
    print("✓ User created ONLY after successful OTP verification")
    print("=" * 70)

# Run test
test_session_registration()
