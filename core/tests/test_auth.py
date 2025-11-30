import pytest
from django.urls import reverse
from core.models import OTP
from core.tests.factories import UserFactory
from unittest.mock import patch

@pytest.mark.django_db
class TestAuthentication:
    
    @patch('core.views.send_email_task.delay')
    def test_registration_success(self, mock_send_email, client):
        url = reverse('core:register')
        response = client.post(url, {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        
        # Should redirect to OTP verification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.get(username='newuser')
        assert response.status_code == 302
        assert response.url == reverse('core:verify_otp', kwargs={'user_id': user.id})
        
        # Check user is inactive
        assert not user.is_active
        
        # Check OTP created
        assert OTP.objects.filter(user=user).exists()
        
        # Check email task called
        mock_send_email.assert_called_once()

    def test_registration_duplicate_email(self, client):
        UserFactory(email='duplicate@example.com')
        url = reverse('core:register')
        
        response = client.post(url, {
            'username': 'newuser2',
            'email': 'duplicate@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        
        assert response.status_code == 200
        assert "A user with this email already exists" in response.content.decode()

    def test_login_success(self, client):
        user = UserFactory(username='loginuser')
        url = reverse('core:login')
        
        response = client.post(url, {
            'username': 'loginuser',
            'password': 'password123',
            'device_fingerprint': 'test_fingerprint_hash',
            'device_metadata': '{}'
        })
        
        # Should redirect to verify_device for new device
        assert response.status_code == 302
        assert response.url == reverse('core:verify_device')
        
        # Check session
        assert int(client.session['pending_device_user_id']) == user.pk

    def test_login_invalid_credentials(self, client):
        url = reverse('core:login')
        response = client.post(url, {
            'username': 'wronguser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert "Invalid username or password" in response.content.decode()
