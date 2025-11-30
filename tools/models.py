from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify


class Tool(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)
    video_url = models.URLField(max_length=500, blank=True, null=True)
    source_code_url = models.URLField(max_length=500, blank=True, null=True)
    detailed_content = CKEditor5Field('Content', config_name='default')
    category = models.CharField(max_length=100, default='General')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tool_posts',
        null=True,
        blank=True
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tools:tool_detail', kwargs={'pk': self.pk})


class PremiumRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    TIER_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    DURATION_CHOICES = [
        (30, '1 Month'),
        (90, '3 Months'),
        (180, '6 Months'),
        (365, '1 Year'),
        (0, 'Lifetime'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='premium_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='basic')
    approved_tier = models.CharField(max_length=20, choices=TIER_CHOICES, blank=True)
    requested_duration = models.PositiveIntegerField(choices=DURATION_CHOICES, default=30)
    approved_duration = models.PositiveIntegerField(null=True, blank=True)
    request_reason = models.TextField(blank=True, help_text="User's reason for requesting premium")
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='premium_requests_reviewed'
    )
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection (visible to user if provided)")
    admin_notes = models.TextField(blank=True, help_text="Internal notes (not visible to user)")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']
        verbose_name_plural = "Premium Requests"
        indexes = [
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"Premium request by {self.user.username} - {self.status}"
    
    def is_pending(self):
        return self.status == 'pending'
    
    def is_approved(self):
        return self.status == 'approved'
    
    def is_rejected(self):
        return self.status == 'rejected'
    
    def get_tier_display(self):
        tier_map = {'basic': 'Basic', 'pro': 'Pro', 'enterprise': 'Enterprise'}
        return tier_map.get(self.requested_tier, 'Basic')
    
    def get_duration_display_text(self):
        duration_map = {30: '1 Month', 90: '3 Months', 180: '6 Months', 365: '1 Year', 0: 'Lifetime'}
        return duration_map.get(self.requested_duration, '1 Month')


class ToolReview(models.Model):
    tool = models.ForeignKey(Tool, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tool_reviews'
    )
    rating = models.PositiveSmallIntegerField()
    review_text = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('tool', 'user')

    def __str__(self):
        return f"Review by {self.user.username} for {self.tool.title}"
