from django import forms
from .models import UserProfile, ContactMessage
from django.core.exceptions import ValidationError

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            if picture.size > 2 * 1024 * 1024:
                raise ValidationError("Profile picture file size must be under 2MB.")
            if not picture.content_type in ['image/jpeg', 'image/png']:
                raise ValidationError("Profile picture must be JPEG or PNG format.")
        return picture
