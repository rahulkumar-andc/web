# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'
from django.views.generic import View
from django.contrib.auth import logout
from django.shortcuts import redirect

class ForceLogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('core:home')

urlpatterns = [
    path('', views.home, name='home'),

    # Auth
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', ForceLogoutView.as_view(), name='logout'),
    # OTP Verification
    path('verify-otp/<int:user_id>/', views.verify_otp, name='verify_otp'),
    path('resend-otp/<int:user_id>/', views.resend_otp, name='resend_otp'),
    
    # 2FA
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('verify-2fa-setup/', views.verify_2fa_setup, name='verify_2fa_setup'),
    path('login-2fa/', views.login_2fa, name='login_2fa'),
    # Device Verification
    path('verify-device/', views.verify_device, name='verify_device'),
    path('resend-device-otp/', views.resend_device_otp, name='resend_device_otp'),
    
    # Security & Session Management
    path('security-logs/', views.security_logs, name='security_logs'),
    path('csp-report/', views.csp_report, name='csp_report'),
    path('active-sessions/', views.active_sessions, name='active_sessions'),
    path('terminate-session/<str:session_key>/', views.terminate_session, name='terminate_session'),
    path('logout-all-sessions/', views.logout_all_sessions, name='logout_all_sessions'),
    # Trusted Devices Management
    path('trusted-devices/', views.trusted_devices, name='trusted_devices'),
    path('rename-device/<int:device_id>/', views.rename_device, name='rename_device'),
    path('revoke-device/<int:device_id>/', views.revoke_device, name='revoke_device'),
    path('block-device/<int:device_id>/', views.block_device, name='block_device'),
    # Services & Blog
    path('services/', views.services_view, name='services'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/create/', views.blog_create, name='blog_create'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('blog/<slug:slug>/edit/', views.blog_update, name='blog_update'),
    path('blog/<slug:slug>/delete/', views.blog_delete, name='blog_delete'),
    
    # Notes
    path('notes/', views.notes_list, name='notes_list'),
    path('notes/upload/', views.note_upload, name='note_upload'),
    path('notes/my-notes/', views.my_notes, name='my_notes'),
    path('notes/<slug:slug>/', views.note_detail, name='note_detail'),
    path('notes/<slug:slug>/download/', views.note_download, name='note_download'),
    path('notes/<slug:slug>/edit/', views.note_edit, name='note_edit'),
    path('notes/<slug:slug>/delete/', views.note_delete, name='note_delete'),

    # Static Pages
    path('contact/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),
    path('achievements/', views.achievements, name='achievements'),
    path('education/', views.education, name='education'),
    path('skills/', views.skills, name='skills'),
    path('gallery/', views.gallery, name='gallery'),
    path('social/', views.social, name='social'),

    # ⭐ Password Reset System
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='core/password_reset.html'
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='core/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
             template_name='core/password_reset_confirm.html'
        ),
        name='password_reset_confirm'),

    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='core/password_reset_complete.html'
         ),
         name='password_reset_complete'),

    path('test-error/<str:code>/', views.test_error_page, name='test_error'),
    
    # Videos
    path('videos/', views.video_list, name='video_list'),
    path('videos/category/<str:category>/', views.video_list, name='video_list_category'),
    path('videos/add/', views.video_add, name='video_add'),
    path('videos/<slug:slug>/', views.video_detail, name='video_detail'),
    path('videos/<slug:slug>/delete/', views.video_delete, name='video_delete'),
]
