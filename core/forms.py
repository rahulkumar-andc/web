import re
import bleach
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from .models import CustomUser, ContactMessage, Service, BlogPost, Note
from django.utils.text import slugify
from django_ckeditor_5.widgets import CKEditor5Widget
from .validators import validate_safe_url, validate_phone_number, sanitize_html


ICON_CHOICES = [
    ('fas fa-code', 'Code'),
    ('fas fa-shield-alt', 'Shield'),
    ('fas fa-laptop', 'Laptop'),
    ('fas fa-cogs', 'Settings'),
    ('fas fa-heart', 'Love ❤️'),
]


class ServiceForm(forms.ModelForm):
    icon = forms.ChoiceField(choices=ICON_CHOICES, label="Icon (FontAwesome)")

    class Meta:
        model = Service
        fields = '__all__'

    class Media:
        js = ('https://kit.fontawesome.com/a076d05399.js',)
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',)
        }

    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        if url:
            validate_safe_url(url)
        return url


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        return bleach.clean(name, tags=[], strip=True)

    def clean_subject(self):
        subject = self.cleaned_data.get('subject', '')
        return bleach.clean(subject, tags=[], strip=True)

    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        return bleach.clean(message, tags=[], strip=True)


class BlogPostForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget())

    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'image_url', 'is_private']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'image_url': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        return bleach.clean(title, tags=[], strip=True)

    def clean_content(self):
        content = self.cleaned_data.get('content', '')
        return sanitize_html(content)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['bio', 'profile_picture', 'twitter_link', 'facebook_link', 'linkedin_link', 'instagram_link']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:
                raise ValidationError("Profile picture file size must be under 2MB.")
            if hasattr(picture, 'content_type'):
                if not picture.content_type in ['image/jpeg', 'image/png']:
                    raise ValidationError("Profile picture must be JPEG or PNG format.")
        return picture

    def clean_bio(self):
        bio = self.cleaned_data.get('bio', '')
        return bleach.clean(bio, tags=[], strip=True)

    def clean_twitter_link(self):
        url = self.cleaned_data.get('twitter_link')
        if url:
            validate_safe_url(url)
        return url

    def clean_facebook_link(self):
        url = self.cleaned_data.get('facebook_link')
        if url:
            validate_safe_url(url)
        return url

    def clean_linkedin_link(self):
        url = self.cleaned_data.get('linkedin_link')
        if url:
            validate_safe_url(url)
        return url

    def clean_instagram_link(self):
        url = self.cleaned_data.get('instagram_link')
        if url:
            validate_safe_url(url)
        return url


class NoteUploadForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ['title', 'description', 'category', 'icon_class', 'icon_image_url', 'file', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter note title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description of the notes'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'icon_class': forms.Select(attrs={'class': 'form-control'}),
            'icon_image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional: Image URL for icon'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.png,.jpg,.jpeg,.zip'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '')
        return bleach.clean(title, tags=[], strip=True)

    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        return bleach.clean(description, tags=[], strip=True)

    def clean_icon_image_url(self):
        url = self.cleaned_data.get('icon_image_url')
        if url:
            validate_safe_url(url)
        return url

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 50 * 1024 * 1024:
                raise ValidationError("File size must be under 50MB.")
            allowed_extensions = ['pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'zip', 'rar']
            ext = file.name.split('.')[-1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        return file

    def clean_thumbnail(self):
        thumbnail = self.cleaned_data.get('thumbnail')
        if thumbnail:
            if thumbnail.size > 5 * 1024 * 1024:
                raise ValidationError("Thumbnail size must be under 5MB.")
            if not thumbnail.content_type in ['image/jpeg', 'image/png', 'image/gif', 'image/webp']:
                raise ValidationError("Thumbnail must be an image file (JPEG, PNG, GIF, WebP).")
        return thumbnail


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone:
            validate_phone_number(phone)
        return phone

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        username = bleach.clean(username, tags=[], strip=True)
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError("Username may only contain letters, numbers, and @/./+/-/_ characters.")
        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long.")
        if len(username) > 30:
            raise ValidationError("Username must be 30 characters or fewer.")
        return username
