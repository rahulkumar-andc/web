import base64
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def get_fernet_key():
    """
    Derive a 32-byte url-safe base64-encoded key from SECRET_KEY.
    """
    # Use SHA-256 to get 32 bytes from SECRET_KEY
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_data(data):
    """
    Encrypts a string using Fernet (AES).
    """
    if not data:
        return None
    f = Fernet(get_fernet_key())
    return f.encrypt(data.encode()).decode()

def decrypt_data(data):
    """
    Decrypts a string using Fernet (AES).
    """
    if not data:
        return None
    try:
        f = Fernet(get_fernet_key())
        return f.decrypt(data.encode()).decode()
    except Exception:
        return None

def hash_otp(otp_code):
    """
    Hashes an OTP code using SHA-256.
    """
    return hashlib.sha256(otp_code.encode()).hexdigest()
