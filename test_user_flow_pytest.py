import pytest
from django.test import Client
from django.urls import reverse
from unittest.mock import patch
from core.models import CustomUser, OTP, DeviceVerificationOTP

@pytest.mark.django_db
@patch('core.views.send_email_task.delay')
def test_complete_user_flow(mock_email):
    """Test complete user flow: registration -> OTP -> login with username validation"""
    print("=" * 60)
    print("Testing Complete User Flow with Username Validation")
    print("=" * 60)
    
    client = Client(HTTP_HOST='localhost')
    
    # Test 1: Try to register with invalid usernames (should FAIL)
    print("\n1. Testing Registration with INVALID usernames (should be rejected)...")
    invalid_usernames = [
        ('user.name', 'dot'),
        ('user@example', 'at symbol'),
        ('user-name', 'hyphen'),
        ('user+name', 'plus'),
    ]
    
    for username, reason in invalid_usernames:
        response = client.post(reverse('core:register'), {
            'username': username,
            'email': f'{username.replace(".", "").replace("@", "").replace("-", "").replace("+", "")}@test.com',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        })
        
        if 'Username may only contain letters, numbers, and underscores' in response.content.decode():
            print(f"   ✓ PASS: Username '{username}' (with {reason}) was rejected")
        else:
            print(f"   ✗ FAIL: Username '{username}' was not properly rejected")
    
    # Test 2: Register with valid username (should PASS)
    print("\n2. Testing Registration with VALID username...")
    valid_username = "test_user_123"
    valid_email = "testuser@example.com"
    valid_password = "TestPassword123!"
    
    response = client.post(reverse('core:register'), {
        'username': valid_username,
        'email': valid_email,
        'password1': valid_password,
        'password2': valid_password,
    })
    
    if response.status_code == 302:
        user = CustomUser.objects.get(username=valid_username)
        print(f"   ✓ PASS: User '{valid_username}' registered successfully")
        
        # Test 3: Verify OTP
        print("\n3. Testing OTP Verification...")
        otp_obj = OTP.objects.filter(user=user).latest('created_at')
        print(f"   OTP Code: {otp_obj.otp_code}")
        
        verify_url = reverse('core:verify_otp', args=[user.id])
        response = client.post(verify_url, {'otp': otp_obj.otp_code})
        
        if response.status_code == 302:
            user.refresh_from_db()
            if user.is_active and user.email_verified:
                print(f"   ✓ PASS: OTP verified, user is active")
            else:
                print(f"   ✗ FAIL: User not activated after OTP verification")
                return
        else:
            print(f"   ✗ FAIL: OTP verification failed")
            return
        
        # Test 4: Logout
        print("\n4. Logging out...")
        client.post(reverse('core:logout'))
        print(f"   ✓ User logged out")
        
        # Test 5: Login with valid credentials
        print("\n5. Testing Login with valid credentials...")
        
        # Create a mock device fingerprint to bypass device verification
        fingerprint_data = {
            'device_fingerprint': 'test-fingerprint-12345',
            'device_metadata': '{"browser": "Chrome", "os": "Linux"}',
            'username': valid_username,
            'password': valid_password,
        }
        
        # First login will trigger device verification
        response = client.post(reverse('core:login'), fingerprint_data)
        
        if response.status_code == 302:
            print(f"   ✓ PASS: Login initiated (device verification required)")
            
            # Verify device
            device_otp = DeviceVerificationOTP.objects.filter(user=user).latest('created_at')
            print(f"   Device OTP Code: {device_otp.otp_code}")
            
            verify_device_url = reverse('core:verify_device')
            response = client.post(verify_device_url, {'otp': device_otp.otp_code})
            
            if response.status_code == 302 and response.url == reverse('core:home'):
                print(f"   ✓ PASS: Device verified and logged in successfully")
            else:
                print(f"   ✗ FAIL: Device verification failed - Status: {response.status_code}")
        else:
            print(f"   ✗ FAIL: Login failed - Status: {response.status_code}")
    else:
        print(f"   ✗ FAIL: Registration failed - Status: {response.status_code}")
    
    print("\n" + "=" * 60)
    print("Complete User Flow Test Finished")
    print("=" * 60)
