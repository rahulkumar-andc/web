from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import BlogPost

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['email']

class BlogSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'slug', 'content', 'author', 'created_at', 'updated_at', 'is_published', 'views', 'cover_image']
        # Note: 'is_published', 'views', 'cover_image' might not be in the model based on my view of models.py.
        # Let's double check model fields from view_file output.
        # BlogPost has: title, slug, content, image_url, author, is_private, created_at, updated_at.
        # It does NOT have: is_published, views, cover_image.
        # It has 'is_private' instead of 'is_published' (inverse logic or different?).
        # It has 'image_url' instead of 'cover_image'.
        # I should adapt to the ACTUAL model.
        
        # Adapting fields:
        fields = ['id', 'title', 'slug', 'content', 'author', 'created_at', 'updated_at', 'is_private', 'image_url']
        read_only_fields = ['slug', 'author', 'created_at', 'updated_at']
