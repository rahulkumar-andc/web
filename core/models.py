from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    PREMIUM_STATUS_CHOICES = [
        ('none', 'None'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ]
    
    PREMIUM_TIER_CHOICES = [
        ('none', 'None'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    ROLE_CHOICES = [
        ('viewer', 'Viewer'),
        ('contributor', 'Contributor'),
        ('moderator', 'Moderator'),
        ('admin', 'Admin'),
        ('super_admin', 'Super Admin'),
    ]
    
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    is_premium = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    premium_request_status = models.CharField(
        max_length=20,
        choices=PREMIUM_STATUS_CHOICES,
        default='none',
    )
    premium_tier = models.CharField(
        max_length=20,
        choices=PREMIUM_TIER_CHOICES,
        default='none',
    )
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    premium_activated_at = models.DateTimeField(null=True, blank=True)
    twitter_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    linkedin_link = models.URLField(blank=True, null=True)
    instagram_link = models.URLField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    login_locked_until = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_user_agent = models.TextField(blank=True)
    
    # TOTP 2FA Fields
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_2fa_enabled = models.BooleanField(default=False)
    
    # User Reputation System
    reputation_score = models.IntegerField(default=100)

    # Purchased/Enrolled Content
    purchased_tools = models.ManyToManyField('tools.Tool', blank=True, related_name='purchasers')
    purchased_notes = models.ManyToManyField('Note', blank=True, related_name='purchasers')

    def __str__(self):
        return self.username
    
    def is_login_locked(self):
        if self.login_locked_until and self.login_locked_until > timezone.now():
            return True
        return False
    
    def reset_login_attempts(self):
        self.failed_login_attempts = 0
        self.login_locked_until = None
        self.save(update_fields=['failed_login_attempts', 'login_locked_until'])
    
    def check_premium_expiry(self):
        if self.is_premium and self.premium_expires_at:
            if self.premium_expires_at <= timezone.now():
                self.is_premium = False
                self.premium_request_status = 'expired'
                self.save(update_fields=['is_premium', 'premium_request_status'])
                return True
        return False
    
    def get_premium_tier_display_name(self):
        tier_names = {
            'none': 'Free',
            'basic': 'Basic Premium',
            'pro': 'Pro Premium',
            'enterprise': 'Enterprise Premium',
        }
        return tier_names.get(self.premium_tier, 'Free')
    
    def get_premium_days_remaining(self):
        if self.premium_expires_at and self.is_premium:
            remaining = self.premium_expires_at - timezone.now()
            return max(0, remaining.days)
        return 0
    
    def has_premium_access(self):
        if not self.is_premium:
            return False
        if self.premium_expires_at and self.premium_expires_at <= timezone.now():
            return False
        return True

    def is_viewer(self):
        return self.role == 'viewer'

    def is_contributor(self):
        return self.role == 'contributor' or self.is_moderator()

    def is_moderator(self):
        return self.role == 'moderator' or self.is_admin_role()

    def is_admin_role(self):
        return self.role == 'admin' or self.is_super_admin()

    def is_super_admin(self):
        return self.role == 'super_admin' or self.is_superuser


class Service(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web Development'),
        ('seo', 'SEO'),
        ('app', 'App Development'),
        ('design', 'UI/UX Design'),
    ]

    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=100)
    image_url = models.URLField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='web')

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    content = CKEditor5Field('Content', config_name='default')
    image_url = models.URLField(max_length=500, blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    is_private = models.BooleanField(default=False)
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


class Note(models.Model):
    CATEGORY_CHOICES = [
        ('python', 'Python'),
        ('c', 'C Programming'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('javascript', 'JavaScript'),
        ('html', 'HTML/CSS'),
        ('sql', 'SQL'),
        ('mongodb', 'MongoDB'),
        ('android', 'Android'),
        ('react', 'React'),
        ('django', 'Django'),
        ('nodejs', 'Node.js'),
        ('dsa', 'Data Structures'),
        ('ml', 'Machine Learning'),
        ('cyber', 'Cybersecurity'),
        ('networking', 'Networking'),
        ('os', 'Operating System'),
        ('dbms', 'DBMS'),
        ('other', 'Other'),
    ]
    
    ICON_CHOICES = [
        ('fa-brands fa-python', 'Python'),
        ('fa-solid fa-c', 'C'),
        ('fa-solid fa-code', 'C++'),
        ('fa-brands fa-java', 'Java'),
        ('fa-brands fa-js', 'JavaScript'),
        ('fa-brands fa-html5', 'HTML'),
        ('fa-solid fa-database', 'SQL/Database'),
        ('fa-brands fa-android', 'Android'),
        ('fa-brands fa-react', 'React'),
        ('fa-brands fa-node-js', 'Node.js'),
        ('fa-solid fa-shield-halved', 'Cybersecurity'),
        ('fa-solid fa-network-wired', 'Networking'),
        ('fa-solid fa-laptop-code', 'Programming'),
        ('fa-solid fa-brain', 'ML/AI'),
        ('fa-solid fa-book', 'Notes'),
        ('fa-solid fa-file-pdf', 'PDF'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, help_text="Short description of the notes")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    icon_class = models.CharField(max_length=100, choices=ICON_CHOICES, default='fa-solid fa-book', help_text="Font Awesome icon class")
    icon_image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Alternative: Image URL for icon (overrides icon_class)")
    file = models.FileField(upload_to='notes/', help_text="Upload PDF, images or document files")
    thumbnail = models.ImageField(upload_to='notes_thumbnails/', blank=True, null=True, help_text="Optional thumbnail image")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    download_count = models.PositiveIntegerField(default=0)
    is_approved = models.BooleanField(default=False, help_text="Admin must approve before showing")
    is_featured = models.BooleanField(default=False, help_text="Show on homepage/featured section")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Note.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('core:note_detail', kwargs={'slug': self.slug})
    
    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def get_file_extension(self):
        if self.file:
            return self.file.name.split('.')[-1].upper()
        return ''
    
    def get_file_size(self):
        if self.file:
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return ''


class OTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.username}"
    
    def is_locked(self):
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False
    
    def is_valid(self):
        return (
            not self.is_used and 
            not self.is_locked() and 
            self.expires_at > timezone.now() and
            self.attempts < 5
        )
    
    def increment_attempts(self):
        self.attempts += 1
        if self.attempts >= 5:
            self.locked_until = timezone.now() + timedelta(minutes=30)
        self.save()


class OTPAttemptLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otp_attempt_logs'
    )
    ip_address = models.GenericIPAddressField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    otp_entered = models.CharField(max_length=10, blank=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        status = "Success" if self.was_successful else "Failed"
        return f"OTP {status} - {self.user.username} from {self.ip_address}"


class LoginAttemptLog(models.Model):
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    attempted_at = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-attempted_at']

    def __str__(self):
        status = "Success" if self.was_successful else "Failed"
        return f"Login {status} - {self.username} from {self.ip_address}"


class SecurityLog(models.Model):
    ACTION_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('login_locked', 'Account Locked'),
        ('logout', 'Logout'),
        ('logout_all', 'Logout All Sessions'),
        ('otp_success', 'OTP Verified'),
        ('otp_failed', 'OTP Failed'),
        ('otp_locked', 'OTP Locked'),
        ('otp_resend', 'OTP Resent'),
        ('password_reset', 'Password Reset'),
        ('password_reset_request', 'Password Reset Request'),
        ('password_change', 'Password Changed'),
        ('premium_request', 'Premium Request'),
        ('premium_approved', 'Premium Approved'),
        ('premium_rejected', 'Premium Rejected'),
        ('premium_cancelled', 'Premium Cancelled'),
        ('premium_revoked', 'Premium Revoked'),
        ('premium_expired', 'Premium Expired'),
        ('premium_upgraded', 'Premium Upgraded'),
        ('registration', 'User Registration'),
        ('profile_update', 'Profile Updated'),
        ('new_device_login', 'New Device Login'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('session_terminated', 'Session Terminated'),
        ('device_trusted', 'Device Trusted'),
        ('device_verification_sent', 'Device Verification Sent'),
        ('device_verification_failed', 'Device Verification Failed'),
        ('device_revoked', 'Device Revoked'),
        ('device_blocked', 'Device Blocked'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - {self.user.username if self.user else 'Unknown'}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


class PremiumHistory(models.Model):
    ACTION_CHOICES = [
        ('activated', 'Premium Activated'),
        ('upgraded', 'Tier Upgraded'),
        ('downgraded', 'Tier Downgraded'),
        ('renewed', 'Premium Renewed'),
        ('expired', 'Premium Expired'),
        ('revoked', 'Premium Revoked'),
        ('extended', 'Duration Extended'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='premium_history'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    previous_tier = models.CharField(max_length=20, blank=True)
    new_tier = models.CharField(max_length=20, blank=True)
    previous_expiry = models.DateTimeField(null=True, blank=True)
    new_expiry = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='premium_actions_performed'
    )
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Premium History"

    def __str__(self):
        return f"{self.user.username} - {self.action} on {self.created_at.strftime('%Y-%m-%d')}"


class UserSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='active_sessions'
    )
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} - {self.device_type or 'Unknown'} - {self.ip_address}"
    
    def parse_user_agent(self):
        ua = self.user_agent.lower()
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            self.device_type = 'Mobile'
        elif 'tablet' in ua or 'ipad' in ua:
            self.device_type = 'Tablet'
        else:
            self.device_type = 'Desktop'
        
        if 'chrome' in ua and 'edg' not in ua:
            self.browser = 'Chrome'
        elif 'firefox' in ua:
            self.browser = 'Firefox'
        elif 'safari' in ua and 'chrome' not in ua:
            self.browser = 'Safari'
        elif 'edg' in ua:
            self.browser = 'Edge'
        else:
            self.browser = 'Other'
        
        if 'windows' in ua:
            self.os = 'Windows'
        elif 'mac' in ua:
            self.os = 'macOS'
        elif 'linux' in ua:
            self.os = 'Linux'
        elif 'android' in ua:
            self.os = 'Android'
        elif 'iphone' in ua or 'ipad' in ua:
            self.os = 'iOS'
        else:
            self.os = 'Other'


class DeviceFingerprint(models.Model):
    TRUST_LEVEL_CHOICES = [
        ('trusted', 'Trusted'),
        ('pending', 'Pending Verification'),
        ('blocked', 'Blocked'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='device_fingerprints'
    )
    fingerprint_hash = models.CharField(max_length=64, db_index=True)
    device_label = models.CharField(max_length=100, blank=True, default='')
    trust_level = models.CharField(
        max_length=20,
        choices=TRUST_LEVEL_CHOICES,
        default='pending'
    )
    is_active = models.BooleanField(default=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-last_seen_at']
        unique_together = ['user', 'fingerprint_hash']
    
    def __str__(self):
        label = self.device_label or f"Device {self.id}"
        return f"{self.user.username} - {label} ({self.trust_level})"
    
    def get_device_info(self):
        return {
            'browser': self.metadata.get('browser', 'Unknown'),
            'os': self.metadata.get('os', 'Unknown'),
            'device_type': self.metadata.get('device_type', 'Unknown'),
        }


class DeviceVerificationOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    fingerprint_hash = models.CharField(max_length=64)
    otp_code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Device OTP for {self.user.username}"
    
    def is_valid(self):
        return (
            not self.is_used and 
            self.expires_at > timezone.now() and
            self.attempts < 5
        )
    
    def increment_attempts(self):
        self.attempts += 1
        self.save(update_fields=['attempts'])
