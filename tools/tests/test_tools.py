import pytest
from django.urls import reverse
from core.tests.factories import UserFactory
from tools.models import Tool, PremiumRequest

@pytest.mark.django_db
class TestToolsApp:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.superuser = UserFactory(username='admin', email='admin@example.com', is_superuser=True, is_staff=True)
        self.user = UserFactory(username='user', email='user@example.com')
        self.user.is_premium = False
        self.user.save()
        
        # Create a tool
        self.tool = Tool.objects.create(
            title='Test Tool', 
            category='web', 
            author=self.superuser, 
            detailed_content="Test Content"
        )

    def test_custom_admin_dashboard_access(self):
        # Superuser can access
        self.client.force_login(self.superuser)
        # Using the custom_admin app's dashboard as it seems to be the main one
        url = reverse('custom_admin:dashboard')
        response = self.client.get(url)
        assert response.status_code == 200
        
        # Regular user cannot access
        self.client.force_login(self.user)
        response = self.client.get(url)
        # Should be 302 (redirect to login or home) or 403
        assert response.status_code != 200

    def test_cancel_premium_request(self):
        # Create a pending premium request for user
        PremiumRequest.objects.create(user=self.user, status='pending')
        self.user.premium_request_status = 'pending'
        self.user.save()

        self.client.force_login(self.user)
        # User cancels premium request
        response = self.client.post(reverse('tools:cancel_premium_request'))
        assert response.status_code == 302
        assert response.url == reverse('tools:premium_request_status')
        
        self.user.refresh_from_db()
        assert self.user.premium_request_status == 'cancelled'
        pr = PremiumRequest.objects.get(user=self.user)
        assert pr.status == 'cancelled'

    def test_manage_tools_view(self):
        self.client.force_login(self.superuser)
        # Check custom_admin urls for manage tools
        url = reverse('custom_admin:tools_list')
        response = self.client.get(url)
        assert response.status_code == 200
        assert self.tool.title in response.content.decode()

    def test_manage_premium_requests_view(self):
        PremiumRequest.objects.create(user=self.user, status='pending')
        self.client.force_login(self.superuser)
        url = reverse('custom_admin:premium_requests')
        response = self.client.get(url)
        assert response.status_code == 200
        assert self.user.username in response.content.decode()

    def test_approve_reject_premium_request(self):
        pr = PremiumRequest.objects.create(user=self.user, status='pending')
        self.client.force_login(self.superuser)
        
        # Approve
        url = reverse('custom_admin:approve_premium', args=[pr.id])
        response = self.client.post(url, {
            'tier': 'pro',
            'duration': 30,
            'admin_notes': 'Approved via test'
        })
        assert response.status_code == 302
        
        pr.refresh_from_db()
        assert pr.status == 'approved'
        
        self.user.refresh_from_db()
        assert self.user.is_premium
        
        # Reject
        pr.status = 'pending'
        pr.save()
        
        url = reverse('custom_admin:reject_premium', args=[pr.id])
        response = self.client.post(url, {
            'rejection_reason': 'Test rejection',
            'admin_notes': 'Rejected via test'
        })
        assert response.status_code == 302
        
        pr.refresh_from_db()
        assert pr.status == 'rejected'
        
        self.user.refresh_from_db()
        assert self.user.premium_request_status == 'rejected'
