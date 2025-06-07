from django.contrib import admin
from .models import Tool, PremiumRequest, ToolReview

@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    search_fields = ('title', 'description')

@admin.register(PremiumRequest)
class PremiumRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('user__username',)

@admin.register(ToolReview)
class ToolReviewAdmin(admin.ModelAdmin):
    list_display = ('tool', 'user', 'rating', 'created_at')
    search_fields = ('tool__title', 'user__username')
    list_filter = ('rating',)
