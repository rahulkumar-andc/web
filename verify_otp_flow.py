import os
import django
from django.test import Client
from django.urls import reverse
from django.core import mail

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.models import CustomUser, OTP

from unittest.mock import patch

@patch('core.views.send_email_task.delay')
def test_otp_flow(mock_email):
    print("Starting OTP Flow Verification...")
    client = Client(HTTP_HOST='localhost')
    
    # 1. Registration
    print("\n1. Testing Registration...")
    username = "test_otp_user"
    email = "test_otp@example.com"
    password = "TestPassword123!"
    
    # Cleanup previous run
    CustomUser.objects.filter(username=username).delete()
    
    register_url = reverse('core:register')
    response = client.post(register_url, {
        'username': username,
        'email': email,
        'password1': password,
        'password2': password,
    })
    
    if response.status_code != 302:
        print(f"FAIL: Registration failed with status {response.status_code}")
        print(response.content.decode())
        return

    user = CustomUser.objects.get(username=username)
    print(f"PASS: User '{username}' created.")
    
    if user.is_active:
        print("FAIL: User should be inactive before OTP verification.")
    else:
        print("PASS: User is inactive as expected.")

    # 2. OTP Generation
    print("\n2. Checking OTP Generation...")
    try:
        otp_obj = OTP.objects.filter(user=user).latest('created_at')
        print(f"PASS: OTP generated: {otp_obj.otp_code}")
    except OTP.DoesNotExist:
        print("FAIL: No OTP generated for user.")
        return

    # 3. OTP Verification
    print("\n3. Testing OTP Verification...")
    verify_url = reverse('core:verify_otp', args=[user.id])
    
    # Test invalid OTP
    response = client.post(verify_url, {'otp': '000000'})
    if "Invalid OTP" in response.content.decode():
        print("PASS: Invalid OTP rejected.")
    else:
        print("FAIL: Invalid OTP was not rejected properly.")

    # Test valid OTP
    response = client.post(verify_url, {'otp': otp_obj.otp_code})
    
    if response.status_code == 302 and response.url == reverse('core:home'):
        print("PASS: Valid OTP accepted and redirected to home.")
    else:
        print(f"FAIL: Valid OTP verification failed. Status: {response.status_code}, URL: {response.url}")
        print(response.content.decode())

    user.refresh_from_db()
    if user.is_active and user.email_verified:
        print("PASS: User is now active and verified.")
    else:
        print("FAIL: User status not updated after verification.")

if __name__ == "__main__":
    test_otp_flow()
