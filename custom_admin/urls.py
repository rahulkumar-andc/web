from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:user_id>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),
    
    path('premium/', views.premium_dashboard, name='premium_dashboard'),
    path('premium/requests/', views.premium_requests, name='premium_requests'),
    path('premium/requests/<int:request_id>/approve/', views.approve_premium, name='approve_premium'),
    path('premium/requests/<int:request_id>/reject/', views.reject_premium, name='reject_premium'),
    path('premium/users/', views.premium_users, name='premium_users'),
    path('premium/users/<int:user_id>/revoke/', views.revoke_premium, name='revoke_premium'),
    path('premium/users/<int:user_id>/extend/', views.extend_premium, name='extend_premium'),
    
    path('tools/', views.tools_list, name='tools_list'),
    path('tools/create/', views.tool_create, name='tool_create'),
    path('tools/<int:tool_id>/edit/', views.tool_edit, name='tool_edit'),
    path('tools/<int:tool_id>/delete/', views.tool_delete, name='tool_delete'),
    
    path('blogs/', views.blog_list, name='blog_list'),
    path('blogs/create/', views.blog_create, name='blog_create'),
    path('blogs/<int:blog_id>/edit/', views.blog_edit, name='blog_edit'),
    path('blogs/<int:blog_id>/delete/', views.blog_delete, name='blog_delete'),
    
    path('security/', views.security_dashboard, name='security_dashboard'),
    path('security/logs/', views.security_logs, name='security_logs'),
    path('security/login-attempts/', views.login_attempts, name='login_attempts'),
    path('security/otp-attempts/', views.otp_attempts, name='otp_attempts'),
    path('security/sessions/', views.active_sessions, name='active_sessions'),
    path('security/sessions/<int:session_id>/terminate/', views.terminate_session, name='terminate_session'),
    
    path('messages/', views.contact_messages, name='contact_messages'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/delete/', views.message_delete, name='message_delete'),
    
    path('services/', views.services_list, name='services_list'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<int:service_id>/edit/', views.service_edit, name='service_edit'),
    path('services/<int:service_id>/delete/', views.service_delete, name='service_delete'),
    
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/analytics/', views.analytics_api, name='analytics_api'),
]
