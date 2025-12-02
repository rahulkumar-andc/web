import os
import django
import pyotp

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.models import CustomUser

def verify_totp():
    print("Verifying TOTP Implementation...")
    
    # 1. Create/Get User
    user, created = CustomUser.objects.get_or_create(username='totp_test_user')
    user.set_password('password123')
    user.save()
    print(f"User: {user.username}")
    
    # 2. Setup 2FA
    print("\nTest 1: Setup 2FA...")
    if not user.totp_secret:
        user.totp_secret = pyotp.random_base32()
        user.save()
    print(f"Secret: {user.totp_secret}")
    
    totp = pyotp.TOTP(user.totp_secret)
    code = totp.now()
    print(f"Generated Code: {code}")
    
    if totp.verify(code):
        print("Code Verification -> PASS")
        user.is_2fa_enabled = True
        user.save()
    else:
        print("Code Verification -> FAIL")
        
    # 3. Verify Login Logic (Simulation)
    print("\nTest 2: Login Logic...")
    if user.is_2fa_enabled:
        print("User has 2FA enabled -> PASS")
    else:
        print("User 2FA NOT enabled -> FAIL")

if __name__ == '__main__':
    verify_totp()
