import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'villen.settings')
django.setup()

from core.validators import PasswordStrengthValidator
from django.core.exceptions import ValidationError

print("=" * 70)
print("PASSWORD VALIDATION TEST")
print("=" * 70)

validator = PasswordStrengthValidator()

# Test invalid passwords
print("\n1. Testing INVALID passwords (should be rejected)...")
invalid_passwords = [
    ("weakpass", "no uppercase, no digit, no special char"),
    ("WEAKPASS", "no lowercase, no digit, no special char"),
    ("WeakPass", "no digit, no special char"),
    ("WeakPass1", "no special char"),
    ("weak@", "too short (< 10 chars)"),
    ("short1@A", "too short (< 10 chars)"),
    ("alllowercase123!", "no uppercase"),
    ("ALLUPPERCASE123!", "no lowercase"),
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
    "Valid#Password99",
]

for password in valid_passwords:
    try:
        validator.validate(password)
        print(f"   ✓ PASS: '{password}' accepted")
    except ValidationError as e:
        print(f"   ✗ FAIL: '{password}' rejected - {e}")

print("\n" + "=" * 70)
print("✅ PASSWORD REQUIREMENTS:")
print("=" * 70)
print("   ✓ Minimum 10 characters")
print("   ✓ At least 1 uppercase letter (A-Z)")
print("   ✓ At least 1 lowercase letter (a-z)")
print("   ✓ At least 1 digit (0-9)")
print("   ✓ At least 1 special character (!@#$%^&*(),.?\":{}|<>)")
print("=" * 70)
