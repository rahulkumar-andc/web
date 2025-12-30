from rest_framework import viewsets, permissions
from .models import BlogPost
from .serializers import BlogSerializer

class BlogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.filter(is_private=False)
    serializer_class = BlogSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
