import pytest
from core.tests.factories import UserFactory, OTPFactory
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
class TestCustomUserModel:
    def test_create_user(self):
        user = UserFactory(username='testuser')
        assert user.username == 'testuser'
        assert user.check_password('password123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        # Using the manager method directly for superuser as factory usually creates normal users
        from django.contrib.auth import get_user_model
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword123'
        )
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_user_roles(self):
        user = UserFactory(role='viewer')
        assert user.is_viewer()
        
        user.role = 'admin'
        assert user.is_admin_role()
        assert user.is_moderator()

    def test_premium_logic(self):
        user = UserFactory()
        assert not user.is_premium
        
        # Grant premium
        user.is_premium = True
        user.premium_tier = 'pro'
        user.premium_expires_at = timezone.now() + timedelta(days=30)
        user.save()
        
        assert user.has_premium_access()
        assert user.get_premium_days_remaining() == 29 # Approx

        # Expire premium
        user.premium_expires_at = timezone.now() - timedelta(days=1)
        user.save()
        
        # Check expiry logic
        is_expired = user.check_premium_expiry()
        assert is_expired
        assert not user.is_premium


@pytest.mark.django_db
class TestOTPModel:
    def test_otp_validity(self):
        otp = OTPFactory()
        assert otp.is_valid()

    def test_otp_expiry(self):
        otp = OTPFactory(expires_at=timezone.now() - timedelta(minutes=1))
        assert not otp.is_valid()

    def test_otp_used(self):
        otp = OTPFactory(is_used=True)
        assert not otp.is_valid()

    def test_otp_lockout(self):
        otp = OTPFactory()
        for _ in range(5):
            otp.increment_attempts()
        
        assert otp.is_locked()
        assert not otp.is_valid()
