from rest_framework import viewsets, permissions
from .models import Tool
from .serializers import ToolSerializer

class ToolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [permissions.AllowAny]
