import pytest
from django.test import RequestFactory
from django.http import HttpResponse
from core.middleware import WAFMiddleware
from core.tests.factories import UserFactory

@pytest.mark.django_db
class TestWAFMiddleware:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse("Success")
        self.middleware = WAFMiddleware(self.get_response)
        self.user = UserFactory()

    def test_clean_request_passes(self):
        request = self.factory.get('/')
        request.user = self.user
        response = self.middleware(request)
        assert response.status_code == 200
        assert response.content == b"Success"

    def test_sqli_blocked(self):
        # Test SQL Injection pattern
        request = self.factory.get('/?q=UNION SELECT 1,2,3')
        request.user = self.user
        response = self.middleware(request)
        assert response.status_code == 403
        assert b"SQL Injection Detected" in response.content

    def test_xss_blocked(self):
        # Test XSS pattern
        request = self.factory.get('/?q=<script>alert(1)</script>')
        request.user = self.user
        response = self.middleware(request)
        assert response.status_code == 403
        assert b"XSS Detected" in response.content

    def test_honeypot_blocked(self):
        request = self.factory.get('/wp-admin/')
        request.user = self.user
        response = self.middleware(request)
        assert response.status_code == 403
        assert b"Suspicious activity detected" in response.content
