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
from core.models import CustomUser, OTP
from core.validators import PasswordStrengthValidator
from django.core.exceptions import ValidationError

print("=" * 70)
print("OTP FLOW & PASSWORD VALIDATION TEST")
print("=" * 70)

# ============================================================================
# PART 1: PASSWORD VALIDATION TEST
# ============================================================================
print("\n" + "=" * 70)
print("PART 1: PASSWORD VALIDATION")
print("=" * 70)

validator = PasswordStrengthValidator()

# Test invalid passwords
print("\n1. Testing INVALID passwords (should be rejected)...")
invalid_passwords = [
    ("weakpass", "no uppercase, no special char"),
    ("WEAKPASS", "no lowercase, no special char"),
    ("WeakPass", "no digit, no special char"),
    ("WeakPass1", "no special char"),
    ("weak@", "too short (< 10 chars)"),
    ("short1@A", "too short (< 10 chars)"),
]

for password, reason in invalid_passwords:
    try:
        validator.validate(password)
        print(f"   ✗ FAIL: '{password}' was accepted ({reason})")
    except ValidationError as e:
        print(f"   ✓ PASS: '{password}' rejected - {reason}")

# Test valid passwords
print("\n2. Testing VALID passwords (should be accepted)...")
valid_passwords = [
    "StrongPass123!",
    "MySecure@Pass1",
    "Test_Password#2024",
    "Complex!Pass9876",
]

for password in valid_passwords:
    try:
        validator.validate(password)
        print(f"   ✓ PASS: '{password}' accepted")
    except ValidationError as e:
        print(f"   ✗ FAIL: '{password}' rejected - {e}")

print("\n✅ Password Validation Requirements:")
print("   • Minimum 10 characters")
print("   • At least 1 uppercase letter")
print("   • At least 1 lowercase letter")
print("   • At least 1 digit")
print("   • At least 1 special character (!@#$%^&*(),.?\":{}|<>)")

# ============================================================================
# PART 2: OTP FLOW TEST
# ============================================================================
print("\n" + "=" * 70)
print("PART 2: OTP FLOW (Registration → OTP → Verification)")
print("=" * 70)

@patch('core.views.send_email_task.delay')
def test_otp_flow(mock_email):
    client = Client(HTTP_HOST='localhost')
    
    # Step 1: Register with valid password
    print("\n1. Testing Registration with valid password...")
    username = "test_otp_user"
    email = "test@example.com"
    password = "ValidPass123!"  # Meets all requirements
    
    # Cleanup
    CustomUser.objects.filter(username=username).delete()
    
    response = client.post(reverse('core:register'), {
        'username': username,
        'email': email,
        'password1': password,
        'password2': password,
    })
    
    if response.status_code != 302:
        print(f"   ✗ FAIL: Registration failed")
        print(f"   Response: {response.content.decode()[:200]}")
        return
    
    user = CustomUser.objects.get(username=username)
    print(f"   ✓ PASS: User '{username}' registered")
    
    if not user.is_active:
        print(f"   ✓ PASS: User is inactive (waiting for OTP)")
    else:
        print(f"   ✗ FAIL: User should be inactive")
    
    # Step 2: Check OTP generation
    print("\n2. Checking OTP Generation...")
    try:
        otp_obj = OTP.objects.filter(user=user).latest('created_at')
        print(f"   ✓ PASS: OTP generated successfully")
        print(f"   OTP Code: {otp_obj.otp_code}")
        print(f"   Expires: {otp_obj.expires_at}")
    except OTP.DoesNotExist:
        print(f"   ✗ FAIL: No OTP generated")
        return
    
    # Step 3: Try wrong OTP
    print("\n3. Testing WRONG OTP (should be rejected)...")
    verify_url = reverse('core:verify_otp', args=[user.id])
    response = client.post(verify_url, {'otp': '000000'})
    
    if "Invalid OTP" in response.content.decode():
        print(f"   ✓ PASS: Wrong OTP rejected")
    else:
        print(f"   ✗ FAIL: Wrong OTP was not rejected")
    
    # Step 4: Try correct OTP
    print("\n4. Testing CORRECT OTP (should be accepted)...")
    response = client.post(verify_url, {'otp': otp_obj.otp_code})
    
    if response.status_code == 302:
        user.refresh_from_db()
        if user.is_active and user.email_verified:
            print(f"   ✓ PASS: OTP verified successfully")
            print(f"   ✓ PASS: User is now active and verified")
        else:
            print(f"   ✗ FAIL: User not activated properly")
    else:
        print(f"   ✗ FAIL: OTP verification failed")
    
    print("\n✅ Complete OTP Flow:")
    print("   1. User registers → account created (inactive)")
    print("   2. OTP sent to email (6-digit code)")
    print("   3. User enters OTP → account activated")
    print("   4. User can now login")

# Run OTP flow test
test_otp_flow()

print("\n" + "=" * 70)
print("TEST COMPLETED")
print("=" * 70)
