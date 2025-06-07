from django import forms
from .models import UserProfile, ContactMessage
from django.core.exceptions import ValidationError
from .models import Service, BlogPost
from django.utils.text import slugify

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
        js = ('https://kit.fontawesome.com/a076d05399.js',)  # your kit
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css',)
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'image_url']  # image field added
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
        }
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'twitter_link', 'facebook_link', 'linkedin_link', 'instagram_link']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:
                raise ValidationError("Profile picture file size must be under 2MB.")
            if not picture.content_type in ['image/jpeg', 'image/png']:
                raise ValidationError("Profile picture must be JPEG or PNG format.")
        return picture
