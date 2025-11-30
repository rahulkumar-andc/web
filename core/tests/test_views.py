import pytest
from django.urls import reverse
from core.tests.factories import UserFactory

@pytest.mark.django_db
class TestPublicViews:
    def test_home_page(self, client):
        url = reverse('core:home')
        response = client.get(url)
        assert response.status_code == 200
        assert 'core/home.html' in [t.name for t in response.templates]

    def test_about_page(self, client):
        url = reverse('core:about')
        response = client.get(url)
        assert response.status_code == 200

    def test_contact_page(self, client):
        url = reverse('core:contact')
        response = client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestProtectedViews:
    def test_profile_redirect_if_not_logged_in(self, client):
        url = reverse('core:profile')
        login_url = reverse('core:login')
        response = client.get(url)
        assert response.status_code == 302
        assert response.url == f"{login_url}?next={url}"

    def test_profile_access_logged_in(self, client):
        user = UserFactory()
        client.force_login(user)
        url = reverse('core:profile')
        response = client.get(url)
        assert response.status_code == 200
        assert 'core/profile.html' in [t.name for t in response.templates]

    def test_admin_panel_access_denied_for_normal_user(self, client):
        user = UserFactory()
        client.force_login(user)
        # Assuming '/panel/' is the custom admin url
        response = client.get('/panel/') 
        # Should be redirected to home or 403
        if response.status_code == 302:
             assert response.url == reverse('core:home')
        else:
             assert response.status_code == 403


@pytest.mark.django_db
class TestErrorViews:
    def test_404_page(self, client):
        response = client.get('/non-existent-url/')
        assert response.status_code == 404
        assert 'core/404.html' in [t.name for t in response.templates]
