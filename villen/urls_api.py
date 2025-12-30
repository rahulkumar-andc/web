from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.api_views import BlogViewSet
from tools.api_views import ToolViewSet

router = DefaultRouter()
router.register(r'blogs', BlogViewSet)
router.register(r'tools', ToolViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('panel/', include('custom_admin.urls')),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
