from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from django.utils.html import format_html
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import CustomUser, Service, BlogPost, ContactMessage, OTP, OTPAttemptLog, LoginAttemptLog, SecurityLog, Note
from .models import Video


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_premium', 'email_verified', 'is_staff', 'is_superuser')
    list_filter = ('is_premium', 'email_verified', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'phone_number')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {
            'fields': ('bio', 'profile_picture', 'phone_number', 'is_premium', 'email_verified', 'premium_request_status')
        }),
        ('Social Links', {
            'fields': ('twitter_link', 'facebook_link', 'linkedin_link', 'instagram_link')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'login_locked_until'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Profile Info', {
            'fields': ('email', 'phone_number',)
        }),
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'show_image', 'show_icon')
    search_fields = ('title', 'description')
    list_filter = ()

    def show_icon(self, obj):
        return format_html('<i class="{}" style="font-size: 18px;"></i>', obj.icon)

    show_icon.short_description = "Icon Preview"

    def show_image(self, obj):
        if obj.image_url:
            return format_html(f'<img src="{obj.image_url}" width="60" height="60" />')
        return "No Image"

    show_image.short_description = "Image Preview"

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


class BlogAdminForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditor5Widget(config_name='default'))

    class Meta:
        model = BlogPost
        fields = '__all__'


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    form = BlogAdminForm
    list_display = ('title', 'author', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_filter = ('created_at', 'updated_at', 'author')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'download_count', 'is_approved', 'is_featured', 'created_at')
    list_filter = ('category', 'is_approved', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('download_count', 'created_at', 'updated_at')
    list_editable = ('is_approved', 'is_featured')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'slug', 'description', 'category', 'author')
        }),
        ('Icon Settings', {
            'fields': ('icon_class', 'icon_image_url', 'thumbnail')
        }),
        ('File', {
            'fields': ('file',)
        }),
        ('Status', {
            'fields': ('is_approved', 'is_featured', 'download_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    list_filter = ()


from django.urls import path
from django.http import HttpResponse
from django.contrib.admin import AdminSite


class CoreAdminSite(AdminSite):
    site_header = 'Villen Admin'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view))
        ]
        return custom_urls + urls

    def dashboard_view(self, request):
        user_count = CustomUser.objects.count()
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

admin_site.register(CustomUser, CustomUserAdmin)
admin_site.register(Service, ServiceAdmin)
admin_site.register(BlogPost, BlogPostAdmin)
admin_site.register(ContactMessage, ContactMessageAdmin)


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at', 'attempts', 'is_used', 'is_locked_display')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('otp_hash', 'created_at')
    
    def is_locked_display(self, obj):
        return obj.is_locked()
    is_locked_display.boolean = True
    is_locked_display.short_description = 'Locked'


@admin.register(OTPAttemptLog)
class OTPAttemptLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'attempted_at', 'was_successful')
    list_filter = ('was_successful', 'attempted_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'ip_address', 'attempted_at', 'was_successful', 'otp_entered')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(LoginAttemptLog)
class LoginAttemptLogAdmin(admin.ModelAdmin):
    list_display = ('username', 'ip_address', 'attempted_at', 'was_successful')
    list_filter = ('was_successful', 'attempted_at')
    search_fields = ('username', 'ip_address')
    readonly_fields = ('username', 'ip_address', 'attempted_at', 'was_successful', 'user_agent')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'action', 'ip_address', 'user_agent', 'details', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# admin.py
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'visibility', 'view_count', 'is_active', 'created_at')
    list_filter = ('category', 'visibility', 'is_active', 'created_at')
    search_fields = ('title', 'description', 'slug')
    prepopulated_fields = {"slug": ("title",)}
