#tools/urls.py
from django.urls import path
from . import views

app_name = 'tools'

from . import admin_views

urlpatterns = [
    path('tools/', views.tools_list, name='tools_list'),
    path('tool/<int:pk>/', views.tool_detail, name='tool_detail'),
    path('tool/<int:pk>/update/', views.tool_update, name='tool_update'),
    path('tool/<int:pk>/delete/', views.tool_delete, name='tool_delete'),
    path('request-premium/', views.request_premium, name='request_premium'),
    path('premium-request-status/', views.premium_request_status, name='premium_request_status'),
    path('cancel-premium-request/', views.cancel_premium_request, name='cancel_premium_request'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-request/<int:request_id>/', views.approve_request, name='approve_request'),
    path('reject-request/<int:request_id>/', views.reject_request, name='reject_request'),

    # Custom admin panel routes
    path('custom-admin/', admin_views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('custom-admin/tools/', admin_views.manage_tools, name='manage_tools'),
    path('custom-admin/premium-requests/', admin_views.manage_premium_requests, name='manage_premium_requests'),
    path('custom-admin/approve-request/<int:request_id>/', admin_views.approve_premium_request, name='admin_approve_request'),
    path('custom-admin/reject-request/<int:request_id>/', admin_views.reject_premium_request, name='admin_reject_request'),
]
