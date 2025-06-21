from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Tool, PremiumRequest, ToolReview
from django.utils import timezone

class ToolsAppTests(TestCase):
    def setUp(self):
        # Create superuser and regular user
        self.superuser = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpass')
        self.user = User.objects.create_user(username='user', email='user@example.com', password='userpass')
        self.user.profile.is_premium = False
        self.user.profile.save()

        # Create a tool
        self.tool = Tool.objects.create(title='Test Tool', category='General', author=self.superuser)

        # Create client instances
        self.client = Client()
        self.client_superuser = Client()
        self.client_superuser.login(username='admin', password='adminpass')
        self.client.login(username='user', password='userpass')

    def test_custom_admin_dashboard_access(self):
        # Superuser can access
        response = self.client_superuser.get(reverse('tools:custom_admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        # Regular user cannot access
        response = self.client.get(reverse('tools:custom_admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_cancel_premium_request(self):
        # Create a pending premium request for user
        PremiumRequest.objects.create(user=self.user, status='pending')
        self.user.profile.premium_request_status = 'pending'
        self.user.profile.save()

        # User cancels premium request
        response = self.client.post(reverse('tools:cancel_premium_request'))
        self.assertRedirects(response, reverse('tools:premium_request_status'))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.premium_request_status, 'cancelled')
        pr = PremiumRequest.objects.get(user=self.user)
        self.assertEqual(pr.status, 'cancelled')

    def test_manage_tools_view(self):
        response = self.client_superuser.get(reverse('tools:manage_tools'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tool.title)

    def test_manage_premium_requests_view(self):
        PremiumRequest.objects.create(user=self.user, status='pending')
        response = self.client_superuser.get(reverse('tools:manage_premium_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_approve_reject_premium_request(self):
        pr = PremiumRequest.objects.create(user=self.user, status='pending')
        # Approve
        response = self.client_superuser.get(reverse('tools:admin_approve_request', args=[pr.id]))
        self.assertRedirects(response, reverse('tools:custom_admin_dashboard'))
        pr.refresh_from_db()
        self.assertEqual(pr.status, 'approved')
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.is_premium)
        # Reject
        pr.status = 'pending'
        pr.save()
        response = self.client_superuser.get(reverse('tools:admin_reject_request', args=[pr.id]))
        self.assertRedirects(response, reverse('tools:custom_admin_dashboard'))
        pr.refresh_from_db()
        self.assertEqual(pr.status, 'rejected')
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.premium_request_status, 'rejected')
