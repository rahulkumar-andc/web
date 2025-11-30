from django.contrib import admin
from django.utils import timezone
from .models import Tool, PremiumRequest, ToolReview


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'category')
    list_filter = ('category', 'created_at')


@admin.register(PremiumRequest)
class PremiumRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_tier', 'requested_duration', 'requested_at', 'reviewed_by', 'reviewed_at')
    list_filter = ('status', 'requested_tier', 'requested_at', 'reviewed_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('requested_at', 'reviewed_at', 'reviewed_by', 'ip_address')
    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'status', 'requested_tier', 'requested_duration', 'request_reason', 'requested_at', 'ip_address')
        }),
        ('Review', {
            'fields': ('reviewed_by', 'reviewed_at', 'approved_tier', 'approved_duration', 'rejection_reason', 'admin_notes')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and obj.status != 'pending' and not obj.reviewed_by:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(ToolReview)
class ToolReviewAdmin(admin.ModelAdmin):
    list_display = ('tool', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('tool__title', 'user__username')
    readonly_fields = ('created_at',)
