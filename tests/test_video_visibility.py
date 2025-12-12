from django.test import TestCase, Client
from django.urls import reverse
from core.models import Video, CustomUser

class VideoVisibilityTest(TestCase):
    def setUp(self):
        # Create users
        self.owner = CustomUser.objects.create_user(username='owner', password='password')
        self.other_user = CustomUser.objects.create_user(username='other', password='password')
        self.superuser = CustomUser.objects.create_superuser(username='admin', password='password')

        # Create videos
        self.public_video = Video.objects.create(
            title='Public Video',
            slug='public-video',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            visibility='public',
            added_by=self.owner
        )
        
        self.private_video = Video.objects.create(
            title='Private Video',
            slug='private-video',
            video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            visibility='private',
            added_by=self.owner
        )

        self.client = Client()

    def test_anonymous_user_visibility(self):
        # 1. Anonymous User
        response = self.client.get(reverse('core:video_list'))
        self.assertIn(self.public_video, response.context['videos'])
        self.assertNotIn(self.private_video, response.context['videos'])

        response = self.client.get(reverse('core:video_detail', kwargs={'slug': self.public_video.slug}))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('core:video_detail', kwargs={'slug': self.private_video.slug}))
        self.assertEqual(response.status_code, 404)

    def test_owner_visibility(self):
        # 2. Owner
        self.client.login(username='owner', password='password')
        response = self.client.get(reverse('core:video_list'))
        self.assertIn(self.public_video, response.context['videos'])
        self.assertIn(self.private_video, response.context['videos'])

        response = self.client.get(reverse('core:video_detail', kwargs={'slug': self.private_video.slug}))
        self.assertEqual(response.status_code, 200)

    def test_other_user_visibility(self):
        # 3. Other User
        self.client.login(username='other', password='password')
        response = self.client.get(reverse('core:video_list'))
        self.assertIn(self.public_video, response.context['videos'])
        self.assertNotIn(self.private_video, response.context['videos'])

        response = self.client.get(reverse('core:video_detail', kwargs={'slug': self.private_video.slug}))
        self.assertEqual(response.status_code, 404)

    def test_superuser_visibility(self):
        # 4. Superuser
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('core:video_list'))
        self.assertIn(self.public_video, response.context['videos'])
        self.assertIn(self.private_video, response.context['videos'])

        response = self.client.get(reverse('core:video_detail', kwargs={'slug': self.private_video.slug}))
        self.assertEqual(response.status_code, 200)
