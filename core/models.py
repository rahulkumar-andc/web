from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse

# models.py
from django.db import models

class Service(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web Development'),
        ('seo', 'SEO'),
        ('app', 'App Development'),
        ('design', 'UI/UX Design'),
        #add more categories as needed

    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='web')

    def __str__(self):
        return self.title

# ⬇️ Import RichTextField from CKEditor
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import CKEditor5Field


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)

    # ⬇️ Upgrade to RichTextField for full HTML, CSS, Code etc.
    content = CKEditor5Field('Content', config_name='default')

    image_url = models.URLField(max_length=500, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:blog_detail', kwargs={'slug': self.slug})


from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    premium_request_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending',
    )
    twitter_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    linkedin_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"
