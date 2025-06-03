from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import Service, BlogPost, UserProfile, ContactMessage

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon')
    search_fields = ('title', 'description')
    list_filter = ()

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'updated_at', 'author')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture')
    search_fields = ('user__username', 'bio')
    list_filter = ()

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ()

# Optional: Custom admin site index with stats (simple example)
from django.urls import path
from django.http import HttpResponse
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.contrib.auth.models import User

class CoreAdminSite(AdminSite):
    site_header = 'Villen Admin'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view))
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        user_count = User.objects.count()
        post_count = BlogPost.objects.count()
        service_count = Service.objects.count()
        html = format_html(
            "<h1>Dashboard Stats</h1>"
            "<p>Users: {}</p>"
            "<p>Blog Posts: {}</p>"
            "<p>Services: {}</p>",
            user_count, post_count, service_count
        )
        return HttpResponse(html)

admin_site = CoreAdminSite(name='core_admin')

admin_site.register(Service, ServiceAdmin)
admin_site.register(BlogPost, BlogPostAdmin)
admin_site.register(UserProfile, UserProfileAdmin)
admin_site.register(ContactMessage, ContactMessageAdmin)
