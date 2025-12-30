from rest_framework import serializers
from .models import Tool

class ToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = ['id', 'title', 'slug', 'image_url', 'category', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['slug', 'created_at', 'updated_at']
