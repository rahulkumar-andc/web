from django import forms
from .models import ToolReview, Tool

class ToolReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, label="Rating")

    class Meta:
        model = ToolReview
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }

class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ['title', 'category', 'detailed_content', 'image_url', 'video_url', 'source_code_url']
        widgets = {
            'detailed_content': forms.Textarea(attrs={'rows': 6}),
        }
