from django.shortcuts import render, redirect, get_object_or_404
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .tasks import send_email_task
from django.conf import settings
from .models import CustomUser, Service, BlogPost, ContactMessage, OTP, OTPAttemptLog, SecurityLog, DeviceFingerprint, DeviceVerificationOTP, Note, Video
from .forms import ContactForm, UserProfileForm, BlogPostForm, NoteUploadForm, VideoForm
from django import forms
import logging
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse, FileResponse, Http404
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
import secrets
import hashlib
import hmac
import json
import pyotp
import qrcode
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

from tools.models import Tool


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def log_security_event(user, action, request, details=None):
    SecurityLog.objects.create(
        user=user,
        action=action,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        details=details or {}
    )


def hash_fingerprint(fingerprint_hash):
    secret_key = settings.SECRET_KEY.encode()
    return hmac.new(secret_key, fingerprint_hash.encode(), hashlib.sha256).hexdigest()


def generate_device_otp():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def custom_login(request):
    from django.contrib.auth.forms import AuthenticationForm
    
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        fingerprint_hash = request.POST.get('device_fingerprint', '')
        metadata_str = request.POST.get('device_metadata', '{}')
        
        try:
            metadata = json.loads(metadata_str)
        except json.JSONDecodeError:
            metadata = {}
        
        if form.is_valid():
            user = form.get_user()
            
            if not fingerprint_hash:
                messages.error(request, 'Device verification failed. Please enable JavaScript and try again.')
                return render(request, 'core/login.html', {'form': form})
            
            hashed_fp = hash_fingerprint(fingerprint_hash)
            
            try:
                device = DeviceFingerprint.objects.get(
                    user=user,
                    fingerprint_hash=hashed_fp,
                    is_active=True
                )
                
                if device.trust_level == 'trusted':
                    device.last_seen_at = timezone.now()
                    device.metadata = metadata
                    device.save(update_fields=['last_seen_at', 'metadata'])
                    
                    if user.is_2fa_enabled:
                        request.session['pending_2fa_user_id'] = user.id
                        return redirect('core:login_2fa')
                    
                    login(request, user)
                    
                    # Reputation Boost
                    user.reputation_score += 1
                    user.save(update_fields=['reputation_score'])
                    
                    log_security_event(user, 'login_success', request, {'device': device.device_label or 'Trusted Device'})
                    messages.success(request, 'Welcome back!')
                    return redirect('core:home')
                    
                elif device.trust_level == 'blocked':
                    log_security_event(user, 'login_failed', request, {'reason': 'blocked_device'})
                    messages.error(request, 'This device has been blocked. Please contact support.')
                    return render(request, 'core/login.html', {'form': AuthenticationForm()})
                    
            except DeviceFingerprint.DoesNotExist:
                pass
            
            DeviceVerificationOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            
            otp_code = generate_device_otp()
            expires_at = timezone.now() + timedelta(minutes=10)
            
            DeviceVerificationOTP.objects.create(
                user=user,
                fingerprint_hash=hashed_fp,
                otp_code=otp_code,
                expires_at=expires_at
            )
            
            request.session['pending_device_user_id'] = user.id
            request.session['pending_fingerprint_hash'] = hashed_fp
            request.session['pending_device_metadata'] = metadata
            
            try:
                send_email_task.delay(
                    'New Device Login - VillenSec',
                    f'A login attempt was made from a new device.\n\nYour verification code is: {otp_code}\n\nThis code expires in 10 minutes.\n\nDevice: {metadata.get("browser", "Unknown")} on {metadata.get("os", "Unknown")}\n\nIf this was not you, please change your password immediately.',
                    [user.email]
                )
            except Exception as e:
                logger.error('Device verification email failed: %s', str(e))
            
            log_security_event(user, 'device_verification_sent', request, {'device_info': metadata})
            messages.info(request, 'New device detected. Please enter the verification code sent to your email.')
            return redirect('core:verify_device')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def verify_device(request):
    user_id = request.session.get('pending_device_user_id')
    fingerprint_hash = request.session.get('pending_fingerprint_hash')
    metadata = request.session.get('pending_device_metadata', {})
    
    if not user_id or not fingerprint_hash:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('core:login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        
        if len(otp_input) != 6 or not otp_input.isdigit():
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'core/verify_device.html')
        
        try:
            otp_obj = DeviceVerificationOTP.objects.filter(
                user=user,
                fingerprint_hash=fingerprint_hash,
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')
            
            if otp_obj.attempts >= 5:
                messages.error(request, 'Too many failed attempts. Please login again.')
                del request.session['pending_device_user_id']
                del request.session['pending_fingerprint_hash']
                return redirect('core:login')
            
            if otp_obj.otp_code == otp_input:
                otp_obj.is_used = True
                otp_obj.save()
                
                device, created = DeviceFingerprint.objects.get_or_create(
                    user=user,
                    fingerprint_hash=fingerprint_hash,
                    defaults={
                        'trust_level': 'trusted',
                        'metadata': metadata,
                        'device_label': f"{metadata.get('browser', 'Unknown')} on {metadata.get('os', 'Unknown')}"
                    }
                )
                
                if not created:
                    device.trust_level = 'trusted'
                    device.metadata = metadata
                    device.last_seen_at = timezone.now()
                    device.save()
                
                del request.session['pending_device_user_id']
                del request.session['pending_fingerprint_hash']
                if 'pending_device_metadata' in request.session:
                    del request.session['pending_device_metadata']
                
                if user.is_2fa_enabled:
                    request.session['pending_2fa_user_id'] = user.id
                    return redirect('core:login_2fa')

                login(request, user)
                
                # Reputation Boost
                user.reputation_score += 1
                user.save(update_fields=['reputation_score'])
                
                log_security_event(user, 'device_trusted', request, {'device_info': metadata})
                log_security_event(user, 'login_success', request, {'new_device': True})
                
                messages.success(request, 'Device verified and trusted. Welcome!')
                return redirect('core:home')
            else:
                otp_obj.increment_attempts()
                log_security_event(user, 'device_verification_failed', request)
                remaining = 5 - otp_obj.attempts
                messages.error(request, f'Invalid verification code. {remaining} attempts remaining.')
                
        except DeviceVerificationOTP.DoesNotExist:
            messages.error(request, 'Verification code expired. Please login again.')
            del request.session['pending_device_user_id']
            del request.session['pending_fingerprint_hash']
            return redirect('core:login')
    
    return render(request, 'core/verify_device.html')


@ratelimit(key='ip', rate='3/m', method='GET', block=True)
def resend_device_otp(request):
    user_id = request.session.get('pending_device_user_id')
    fingerprint_hash = request.session.get('pending_fingerprint_hash')
    metadata = request.session.get('pending_device_metadata', {})
    
    if not user_id or not fingerprint_hash:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('core:login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    DeviceVerificationOTP.objects.filter(user=user, fingerprint_hash=fingerprint_hash).update(is_used=True)
    
    otp_code = generate_device_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    DeviceVerificationOTP.objects.create(
        user=user,
        fingerprint_hash=fingerprint_hash,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    try:
        send_email_task.delay(
            'New Verification Code - VillenSec',
            f'Your new device verification code is: {otp_code}\n\nThis code expires in 10 minutes.',
            [user.email]
        )
        messages.success(request, 'A new verification code has been sent to your email.')
    except Exception as e:
        logger.error('Device verification email failed: %s', str(e))
        messages.error(request, 'Failed to send verification code. Please try again.')
    
    return redirect('core:verify_device')


def home(request):
    tools = Tool.objects.all().order_by('-created_at')[:5]
    return render(request, 'core/home.html', {'tools': tools})


@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            try:
                send_email_task.delay(
                    f"New contact message: {contact_message.subject}",
                    f"From: {contact_message.name} <{contact_message.email}>\n\n{contact_message.message}",
                    [settings.DEFAULT_FROM_EMAIL]
                )
            except Exception as e:
                logger.error('Email delivery failed: %s', str(e))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Your message has been sent successfully.'})
            else:
                messages.success(request, 'Your message has been sent successfully.')
                return redirect('core:home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = form.errors.as_json()
                return JsonResponse({'success': False, 'message': 'There were errors in the form.', 'errors': errors})
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})


def is_superuser(user):
    return user.is_superuser


@login_required
@user_passes_test(lambda u: u.is_superuser)
def blog_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.author = request.user
            blog_post.save()
            messages.success(request, 'Blog post created successfully.')
            return redirect('core:blog_list')
    else:
        form = BlogPostForm()
    return render(request, 'core/blog_form.html', {'form': form, 'title': 'Create Blog Post'})


@login_required
def blog_update(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    if request.user != blog_post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('core:blog_detail', slug=slug)
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=blog_post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Blog post updated successfully.')
            return redirect('core:blog_detail', slug=slug)
    else:
        form = BlogPostForm(instance=blog_post)
    return render(request, 'core/blog_form.html', {'form': form, 'title': 'Edit Blog Post'})


@login_required
def blog_delete(request, slug):
    blog_post = get_object_or_404(BlogPost, slug=slug)
    if request.user != blog_post.author and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('core:blog_detail', slug=slug)
    if request.method == 'POST':
        blog_post.delete()
        messages.success(request, 'Blog post deleted successfully.')
        return redirect('core:blog_list')
    return render(request, 'core/confirm_delete.html', {'object': blog_post, 'title': 'Delete Blog Post'})


def generate_secure_otp():
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def check_registration_rate_limit(request):
    ip = get_client_ip(request)
    cache_key = f'register_limit_{ip}'
    attempts = cache.get(cache_key, 0)
    if attempts >= 5:
        return False
    cache.set(cache_key, attempts + 1, 3600)
    return True


@ratelimit(key='ip', rate='5/h', method='POST', block=False)
def register(request):
    if request.method == 'POST':
        if getattr(request, 'limited', False):
            messages.error(request, 'Too many registration attempts. Please try again later.')
            return render(request, 'core/register.html', {'form': CustomUserCreationForm()})
        
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Check if username already exists
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            
            if CustomUser.objects.filter(username=username).exists():
                form.add_error('username', 'A user with this username already exists.')
                return render(request, 'core/register.html', {'form': form})
            
            if CustomUser.objects.filter(email=email).exists():
                form.add_error('email', 'A user with this email already exists.')
                return render(request, 'core/register.html', {'form': form})
            
            # Store registration data in session (NOT in database yet)
            request.session['pending_registration_username'] = username
            request.session['pending_registration_email'] = email
            request.session['pending_registration_password'] = form.cleaned_data['password1']
            request.session['pending_registration_phone'] = form.cleaned_data.get('phone_number', '')

            # Generate OTP and store in session
            otp_code = generate_secure_otp()
            request.session['pending_registration_otp'] = otp_code
            request.session['pending_registration_otp_expires'] = (timezone.now() + timedelta(minutes=10)).isoformat()
            request.session['pending_registration_otp_attempts'] = 0
            
            # Send OTP email
            try:
                send_email_task.delay(
                    'Your OTP Code - VillenSec',
                    f'Your OTP code is {otp_code}. It expires in 10 minutes.\n\nIf you did not request this, please ignore this email.',
                    [email]
                )
            except Exception as e:
                logger.error('OTP email delivery failed: %s', str(e))

            messages.success(request, 'Please enter the OTP sent to your email to complete registration.')
            return redirect('core:verify_otp', user_id=0)  # user_id=0 indicates session-based

    else:
        form = CustomUserCreationForm()

    return render(request, 'core/register.html', {'form': form})


def check_otp_rate_limit(user_id, ip_address):
    cache_key = f'otp_attempts_{user_id}_{ip_address}'
    attempts = cache.get(cache_key, 0)
    if attempts >= 5:
        return False, attempts
    return True, attempts


def increment_otp_attempts(user_id, ip_address):
    cache_key = f'otp_attempts_{user_id}_{ip_address}'
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, 1800)
    return attempts


def clear_otp_attempts(user_id, ip_address):
    cache_key = f'otp_attempts_{user_id}_{ip_address}'
    cache.delete(cache_key)


def verify_otp(request, user_id):
    # Check if this is a session-based registration (user_id=0)
    is_session_based = (user_id == 0)
    
    if is_session_based:
        # Session-based registration - check if session data exists
        if 'pending_registration_otp' not in request.session:
            messages.error(request, 'Registration session expired. Please register again.')
            return redirect('core:register')
        
        email = request.session.get('pending_registration_email')
        ip_address = get_client_ip(request)
        
        # Rate limiting for session-based OTP
        attempts = request.session.get('pending_registration_otp_attempts', 0)
        remaining_attempts = max(0, 5 - attempts)
        
        if attempts >= 5:
            messages.error(request, 'Too many failed attempts. Please register again.')
            # Clear session data
            for key in list(request.session.keys()):
                if key.startswith('pending_registration_'):
                    del request.session[key]
            return redirect('core:register')
        
        if request.method == 'POST':
            otp_input = request.POST.get('otp', '').strip()
            
            if len(otp_input) != 6 or not otp_input.isdigit():
                messages.error(request, 'Please enter a valid 6-digit OTP.')
                return render(request, 'core/verify_otp.html', {
                    'user_id': user_id,
                    'remaining_attempts': remaining_attempts
                })
            
            # Check OTP expiry
            otp_expires_str = request.session.get('pending_registration_otp_expires')
            if not otp_expires_str or timezone.now() > timezone.datetime.fromisoformat(otp_expires_str):
                messages.error(request, 'OTP has expired. Please register again.')
                for key in list(request.session.keys()):
                    if key.startswith('pending_registration_'):
                        del request.session[key]
                return redirect('core:register')
            
            stored_otp = request.session.get('pending_registration_otp')
            
            if stored_otp == otp_input:
                # OTP is correct - NOW create the user in database
                username = request.session.get('pending_registration_username')
                email = request.session.get('pending_registration_email')
                password = request.session.get('pending_registration_password')
                phone = request.session.get('pending_registration_phone', '')
                
                # Final check if username/email is still available
                if CustomUser.objects.filter(username=username).exists():
                    messages.error(request, 'Username is no longer available. Please register again.')
                    for key in list(request.session.keys()):
                        if key.startswith('pending_registration_'):
                            del request.session[key]
                    return redirect('core:register')
                
                if CustomUser.objects.filter(email=email).exists():
                    messages.error(request, 'Email is no longer available. Please register again.')
                    for key in list(request.session.keys()):
                        if key.startswith('pending_registration_'):
                            del request.session[key]
                    return redirect('core:register')
                
                # Create user
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                user.phone_number = phone
                user.is_active = True
                user.email_verified = True
                user.save()
                
                # Log security event
                log_security_event(
                    user=user,
                    action='registration',
                    request=request,
                    details={'email': user.email, 'username': user.username}
                )
                log_security_event(user, 'otp_success', request)
                
                # Clear session data
                for key in list(request.session.keys()):
                    if key.startswith('pending_registration_'):
                        del request.session[key]
                
                # Login user
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, 'Account verified successfully. You are now logged in.')
                return redirect('core:home')
            else:
                # Wrong OTP
                request.session['pending_registration_otp_attempts'] = attempts + 1
                remaining = max(0, 5 - (attempts + 1))
                
                if remaining == 0:
                    messages.error(request, 'Too many failed attempts. Please register again.')
                    for key in list(request.session.keys()):
                        if key.startswith('pending_registration_'):
                            del request.session[key]
                    return redirect('core:register')
                else:
                    messages.error(request, f'Invalid OTP. {remaining} attempts remaining.')
                
                return render(request, 'core/verify_otp.html', {
                    'user_id': user_id,
                    'remaining_attempts': remaining,
                    'locked': remaining == 0
                })
        
        return render(request, 'core/verify_otp.html', {
            'user_id': user_id,
            'remaining_attempts': remaining_attempts
        })
    
    # Original database-based flow (for backward compatibility with existing users)
    user = get_object_or_404(CustomUser, id=user_id)
    ip_address = get_client_ip(request)
    
    can_attempt, current_attempts = check_otp_rate_limit(user_id, ip_address)
    remaining_attempts = max(0, 5 - current_attempts)
    
    if not can_attempt:
        OTPAttemptLog.objects.create(
            user=user,
            ip_address=ip_address,
            was_successful=False,
            otp_entered='RATE_LIMITED'
        )
        log_security_event(user, 'otp_locked', request, {'reason': 'rate_limit_exceeded'})
        messages.error(request, 'Too many failed attempts. Please try again in 30 minutes or request a new OTP.')
        return render(request, 'core/verify_otp.html', {
            'user_id': user_id, 
            'locked': True,
            'remaining_attempts': 0
        })
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        
        if len(otp_input) != 6 or not otp_input.isdigit():
            messages.error(request, 'Please enter a valid 6-digit OTP.')
            return render(request, 'core/verify_otp.html', {
                'user_id': user_id,
                'remaining_attempts': remaining_attempts
            })
        
        try:
            otp_obj = OTP.objects.filter(
                user=user, 
                is_used=False,
                expires_at__gt=timezone.now()
            ).latest('created_at')
            
            if otp_obj.is_locked():
                messages.error(request, 'OTP is locked due to too many failed attempts. Please request a new OTP.')
                return render(request, 'core/verify_otp.html', {
                    'user_id': user_id,
                    'locked': True,
                    'remaining_attempts': 0
                })
            
            if otp_obj.otp_code == otp_input:
                otp_obj.is_used = True
                otp_obj.save()
                
                user.is_active = True
                user.email_verified = True
                user.save()
                
                clear_otp_attempts(user_id, ip_address)
                
                OTPAttemptLog.objects.create(
                    user=user,
                    ip_address=ip_address,
                    was_successful=True,
                    otp_entered=hashlib.sha256(otp_input.encode()).hexdigest()[:10]
                )
                log_security_event(user, 'otp_success', request)
                
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                messages.success(request, 'Account verified successfully. You are now logged in.')
                return redirect('core:home')
            else:
                otp_obj.increment_attempts()
                attempts = increment_otp_attempts(user_id, ip_address)
                remaining = max(0, 5 - attempts)
                
                OTPAttemptLog.objects.create(
                    user=user,
                    ip_address=ip_address,
                    was_successful=False,
                    otp_entered=hashlib.sha256(otp_input.encode()).hexdigest()[:10]
                )
                log_security_event(user, 'otp_failed', request, {'attempts': attempts})
                
                if remaining == 0:
                    messages.error(request, 'Too many failed attempts. Please try again in 30 minutes.')
                else:
                    messages.error(request, f'Invalid OTP. {remaining} attempts remaining.')
                
                return render(request, 'core/verify_otp.html', {
                    'user_id': user_id,
                    'remaining_attempts': remaining,
                    'locked': remaining == 0
                })
                
        except OTP.DoesNotExist:
            messages.error(request, 'No valid OTP found. Please request a new one.')
            
    return render(request, 'core/verify_otp.html', {
        'user_id': user_id,
        'remaining_attempts': remaining_attempts
    })


@ratelimit(key='ip', rate='3/h', method='POST', block=False)
def resend_otp(request, user_id):
    if getattr(request, 'limited', False):
        messages.error(request, 'Too many OTP requests. Please try again later.')
        return redirect('core:verify_otp', user_id=user_id)
    
    # Check if this is session-based registration
    if user_id == 0:
        # Session-based registration
        if 'pending_registration_email' not in request.session:
            messages.error(request, 'Registration session expired. Please register again.')
            return redirect('core:register')
        
        email = request.session.get('pending_registration_email')
        
        # Generate new OTP
        otp_code = generate_secure_otp()
        request.session['pending_registration_otp'] = otp_code
        request.session['pending_registration_otp_expires'] = (timezone.now() + timedelta(minutes=10)).isoformat()
        request.session['pending_registration_otp_attempts'] = 0  # Reset attempts
        
        try:
            send_email_task.delay(
                'Your New OTP Code - VillenSec',
                f'Your new OTP code is {otp_code}. It expires in 10 minutes.\n\nIf you did not request this, please ignore this email.',
                [email]
            )
            messages.success(request, 'A new OTP has been sent to your email.')
        except Exception as e:
            logger.error('OTP email delivery failed: %s', str(e))
            messages.error(request, 'Failed to send OTP. Please try again.')
        
        return redirect('core:verify_otp', user_id=0)
    
    # Database-based flow (backward compatibility)
    user = get_object_or_404(CustomUser, id=user_id)
    ip_address = get_client_ip(request)
    
    if user.is_active and user.email_verified:
        messages.info(request, 'Your account is already verified.')
        return redirect('core:login')
    
    OTP.objects.filter(user=user).update(is_used=True)
    clear_otp_attempts(user_id, ip_address)
    
    otp_code = generate_secure_otp()
    expires_at = timezone.now() + timedelta(minutes=10)
    
    OTP.objects.create(
        user=user,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    try:
        send_email_task.delay(
            'Your New OTP Code - VillenSec',
            f'Your new OTP code is {otp_code}. It expires in 10 minutes.\n\nIf you did not request this, please ignore this email.',
            [user.email]
        )
        messages.success(request, 'A new OTP has been sent to your email.')
    except Exception as e:
        logger.error('OTP email delivery failed: %s', str(e))
        messages.error(request, 'Failed to send OTP. Please try again.')
    
    return redirect('core:verify_otp', user_id=user_id)


def services_view(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    services = Service.objects.all()

    if query:
        services = services.filter(title__icontains=query)

    if category:
        services = services.filter(category=category)

    context = {
        'services': services,
        'query': query,
        'category': category,
        'categories': Service.CATEGORY_CHOICES,
    }
    return render(request, 'core/services.html', context)


def blog_list(request):
    if request.user.is_authenticated and request.user.is_superuser:
        posts = BlogPost.objects.all().order_by('-created_at')
    else:
        posts = BlogPost.objects.filter(is_private=False).order_by('-created_at')
    return render(request, 'core/blog_list.html', {'posts': posts})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if post.is_private and (not request.user.is_authenticated or not request.user.is_superuser):
        return HttpResponse("You do not have permission to view this private blog post.", status=403)
    return render(request, 'core/blog_detail.html', {'post': post})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'core/profile.html', {'form': form})


def custom_404_view(request, exception):
    return render(request, 'core/404.html', status=404)


def custom_500_view(request):
    return render(request, 'core/500.html', status=500)


def about(request):
    return render(request, 'core/about.html')


def achievements(request):
    return render(request, 'core/achievements.html')


def education(request):
    return render(request, 'core/education.html')


def skills(request):
    return render(request, 'core/skills.html')


def gallery(request):
    return render(request, 'core/gallery.html')


def social(request):
    return render(request, 'core/social.html')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def security_logs(request):
    logs = SecurityLog.objects.all()[:100]
    return render(request, 'core/security_logs.html', {'logs': logs})


@login_required
def active_sessions(request):
    from .models import UserSession
    from django.contrib.sessions.models import Session
    
    current_session_key = request.session.session_key
    
    UserSession.objects.filter(
        session_key=current_session_key
    ).update(is_current=True)
    
    UserSession.objects.filter(
        user=request.user
    ).exclude(session_key=current_session_key).update(is_current=False)
    
    sessions = UserSession.objects.filter(user=request.user)
    
    valid_sessions = []
    for user_session in sessions:
        try:
            Session.objects.get(session_key=user_session.session_key)
            valid_sessions.append(user_session)
        except Session.DoesNotExist:
            user_session.delete()
    
    context = {
        'sessions': valid_sessions,
        'current_session_key': current_session_key,
    }
    return render(request, 'core/active_sessions.html', context)


@login_required
def terminate_session(request, session_key):
    from .models import UserSession, SecurityLog
    from django.contrib.sessions.models import Session
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:active_sessions')
    
    if session_key == request.session.session_key:
        messages.error(request, 'Cannot terminate your current session. Use logout instead.')
        return redirect('core:active_sessions')
    
    try:
        user_session = UserSession.objects.get(
            user=request.user,
            session_key=session_key
        )
        
        try:
            session = Session.objects.get(session_key=session_key)
            session.delete()
        except Session.DoesNotExist:
            pass
        
        SecurityLog.objects.create(
            user=request.user,
            action='session_terminated',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            details={
                'terminated_session': session_key[:10] + '...',
                'device': user_session.device_type,
                'browser': user_session.browser
            }
        )
        
        user_session.delete()
        messages.success(request, 'Session terminated successfully.')
        
    except UserSession.DoesNotExist:
        messages.error(request, 'Session not found.')
    
    return redirect('core:active_sessions')


@login_required
def logout_all_sessions(request):
    from .models import UserSession, SecurityLog
    from django.contrib.sessions.models import Session
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:active_sessions')
    
    current_session_key = request.session.session_key
    
    other_sessions = UserSession.objects.filter(
        user=request.user
    ).exclude(session_key=current_session_key)
    
    count = 0
    for user_session in other_sessions:
        try:
            session = Session.objects.get(session_key=user_session.session_key)
            session.delete()
            count += 1
        except Session.DoesNotExist:
            pass
        user_session.delete()
    
    SecurityLog.objects.create(
        user=request.user,
        action='logout_all',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        details={'sessions_terminated': count}
    )
    
    messages.success(request, f'Successfully logged out from {count} other device(s).')
    return redirect('core:active_sessions')


@login_required
def trusted_devices(request):
    devices = DeviceFingerprint.objects.filter(user=request.user, is_active=True)
    return render(request, 'core/trusted_devices.html', {'devices': devices})


@login_required
def rename_device(request, device_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:trusted_devices')
    
    try:
        device = DeviceFingerprint.objects.get(id=device_id, user=request.user)
        new_label = request.POST.get('device_label', '').strip()
        
        if new_label and len(new_label) <= 100:
            device.device_label = new_label
            device.save(update_fields=['device_label'])
            messages.success(request, 'Device renamed successfully.')
        else:
            messages.error(request, 'Please provide a valid device name (max 100 characters).')
            
    except DeviceFingerprint.DoesNotExist:
        messages.error(request, 'Device not found.')
    
    return redirect('core:trusted_devices')


@login_required
def revoke_device(request, device_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:trusted_devices')
    
    try:
        device = DeviceFingerprint.objects.get(id=device_id, user=request.user)
        device_label = device.device_label or 'Unknown device'
        
        device.is_active = False
        device.trust_level = 'blocked'
        device.save(update_fields=['is_active', 'trust_level'])
        
        log_security_event(request.user, 'device_revoked', request, {
            'device_label': device_label,
            'device_id': device_id
        })
        
        messages.success(request, f'Device "{device_label}" has been revoked.')
        
    except DeviceFingerprint.DoesNotExist:
        messages.error(request, 'Device not found.')
    
    return redirect('core:trusted_devices')


@login_required
def block_device(request, device_id):
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('core:trusted_devices')
    
    try:
        device = DeviceFingerprint.objects.get(id=device_id, user=request.user)
        device_label = device.device_label or 'Unknown device'
        
        device.trust_level = 'blocked'
        device.save(update_fields=['trust_level'])
        
        log_security_event(request.user, 'device_blocked', request, {
            'device_label': device_label,
            'device_id': device_id
        })
        
        messages.success(request, f'Device "{device_label}" has been blocked. It will require verification on next login.')
        
    except DeviceFingerprint.DoesNotExist:
        messages.error(request, 'Device not found.')
    
    return redirect('core:trusted_devices')


def notes_list(request):
    category = request.GET.get('category', '')
    notes = Note.objects.filter(is_approved=True)
    
    if category:
        notes = notes.filter(category=category)
    
    categories = Note.CATEGORY_CHOICES
    
    return render(request, 'core/notes_list.html', {
        'notes': notes,
        'categories': categories,
        'selected_category': category,
    })


def note_detail(request, slug):
    note = get_object_or_404(Note, slug=slug, is_approved=True)
    related_notes = Note.objects.filter(
        category=note.category, 
        is_approved=True
    ).exclude(pk=note.pk)[:4]
    
    return render(request, 'core/note_detail.html', {
        'note': note,
        'related_notes': related_notes,
    })


def note_download(request, slug):
    note = get_object_or_404(Note, slug=slug, is_approved=True)
    
    if not note.file:
        raise Http404("File not found")
    
    try:
        file_handle = note.file.open('rb')
        note.increment_download()
        
        filename = note.file.name.split('/')[-1]
        response = FileResponse(
            file_handle,
            as_attachment=True,
            filename=filename
        )
        return response
    except FileNotFoundError:
        raise Http404("File not found")
    except Exception as e:
        logger.error(f"Error downloading note {slug}: {str(e)}")
        raise Http404("Error accessing file")


@login_required
def note_upload(request):
    if request.method == 'POST':
        form = NoteUploadForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.is_approved = False
            note.save()
            
            log_security_event(request.user, 'note_uploaded', request, {
                'note_title': note.title,
                'note_id': note.pk
            })
            
            messages.success(request, 'Your notes have been uploaded successfully! They will be visible after admin approval.')
            return redirect('core:my_notes')
    else:
        form = NoteUploadForm()
    
    return render(request, 'core/note_upload.html', {'form': form})


@login_required
def my_notes(request):
    notes = Note.objects.filter(author=request.user)
    return render(request, 'core/my_notes.html', {'notes': notes})


@login_required
def note_edit(request, slug):
    note = get_object_or_404(Note, slug=slug, author=request.user)
    
    if request.method == 'POST':
        form = NoteUploadForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            note = form.save(commit=False)
            note.is_approved = False
            note.save()
            messages.success(request, 'Note updated successfully! It will require re-approval.')
            return redirect('core:my_notes')
    else:
        form = NoteUploadForm(instance=note)
    
    return render(request, 'core/note_upload.html', {'form': form, 'editing': True, 'note': note})


@login_required
def note_delete(request, slug):
    note = get_object_or_404(Note, slug=slug, author=request.user)
    
    if request.method == 'POST':
        note_title = note.title
        note.delete()
        messages.success(request, f'Note "{note_title}" has been deleted.')
        return redirect('core:my_notes')
    
    return render(request, 'core/note_confirm_delete.html', {'note': note})


@csrf_exempt
@require_POST
def csp_report(request):
    """
    Endpoint to receive CSP violation reports.
    """
    try:
        report_data = json.loads(request.body)
        csp_report = report_data.get('csp-report', {})
        
        # Log the violation
        SecurityLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='csp_violation',
            ip_address=request.META.get('REMOTE_ADDR', '0.0.0.0'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            details=csp_report
        )
        
        # Decrease reputation for CSP violation
        if request.user.is_authenticated:
            request.user.reputation_score -= 5
            request.user.save(update_fields=['reputation_score'])
        
        return JsonResponse({'status': 'ok'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def setup_2fa(request):
    if request.user.is_2fa_enabled:
        messages.info(request, 'Two-factor authentication is already enabled.')
        return redirect('core:profile')
    
    if not request.user.totp_secret:
        request.user.totp_secret = pyotp.random_base32()
        request.user.save(update_fields=['totp_secret'])
    
    # Generate QR Code
    totp = pyotp.TOTP(request.user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=request.user.email,
        issuer_name='VillenSec'
    )
    
    qr = qrcode.make(provisioning_uri)
    stream = BytesIO()
    qr.save(stream)
    qr_image_base64 = base64.b64encode(stream.getvalue()).decode('utf-8')
    
    return render(request, 'core/setup_2fa.html', {
        'qr_image_base64': qr_image_base64,
        'secret_key': request.user.totp_secret
    })


@login_required
def verify_2fa_setup(request):
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        totp = pyotp.TOTP(request.user.totp_secret)
        
        if totp.verify(otp_code):
            request.user.is_2fa_enabled = True
            request.user.save(update_fields=['is_2fa_enabled'])
            messages.success(request, 'Two-factor authentication enabled successfully!')
            return redirect('core:profile')
        else:
            messages.error(request, 'Invalid OTP code. Please try again.')
            return redirect('core:setup_2fa')
    
    return redirect('core:setup_2fa')



@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_2fa(request):
    user_id = request.session.get('pending_2fa_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please login again.')
        return redirect('core:login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        totp = pyotp.TOTP(user.totp_secret)
        
        if totp.verify(otp_code):
            login(request, user)
            del request.session['pending_2fa_user_id']
            
            # Reputation Boost
            user.reputation_score += 1
            user.save(update_fields=['reputation_score'])
            
            log_security_event(user, 'login_success', request, {'method': '2fa_totp'})
            messages.success(request, 'Welcome back!')
            return redirect('core:home')
        else:
            messages.error(request, 'Invalid OTP code.')
            log_security_event(user, 'login_failed', request, {'reason': 'invalid_2fa'})
            
            # Reputation Penalty
            user.reputation_score -= 5
            user.save(update_fields=['reputation_score'])
            
    return render(request, 'core/login_2fa.html')


def custom_400_view(request, exception=None):
    return render(request, 'core/400.html', status=400)


def custom_403_view(request, exception=None):
    return render(request, 'core/403.html', status=403)


def test_error_page(request, code):
    return render(request, f'core/{code}.html')


def video_list(request, category=None):
    categories = Video.CATEGORY_CHOICES
    
    # Base query: Active videos
    videos = Video.objects.filter(is_active=True)
    
    # Filter by visibility
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Superuser sees all active videos
            pass
        else:
            # Authenticated users see public videos AND their own private videos
            from django.db.models import Q
            videos = videos.filter(
                Q(visibility='public') | 
                Q(visibility='private', added_by=request.user)
            )
    else:
        # Anonymous users only see public videos
        videos = videos.filter(visibility='public')
    
    if category:
        videos = videos.filter(category=category)
        category_display = dict(categories).get(category, category.title())
    else:
        category_display = 'All Videos'
    
    return render(request, 'core/video_list.html', {
        'videos': videos,
        'categories': categories,
        'current_category': category,
        'category_display': category_display,
    })


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def video_add(request):
    if request.method == 'POST':
        form = VideoForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.added_by = request.user
            video.save()
            messages.success(request, f'Video "{video.title}" added successfully!')
            return redirect('core:video_list_category', category=video.category)
    else:
        form = VideoForm()
    
    return render(request, 'core/video_add.html', {'form': form})


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def video_delete(request, slug):
    video = get_object_or_404(Video, slug=slug)
    
    if request.method == 'POST':
        category = video.category
        video_title = video.title
        video.delete()
        messages.success(request, f'Video "{video_title}" deleted successfully!')
        return redirect('core:video_list_category', category=category)
    
    return render(request, 'core/video_confirm_delete.html', {'video': video})


def video_detail(request, slug):
    video = get_object_or_404(Video, slug=slug, is_active=True)
    
    # Check visibility
    if video.visibility == 'private':
        if not request.user.is_authenticated:
            raise Http404("Video not found")
        
        if not request.user.is_superuser and video.added_by != request.user:
            raise Http404("Video not found")
    
    viewed_videos = request.session.get('viewed_videos', [])
    if video.id not in viewed_videos:
        video.increment_view()
        viewed_videos.append(video.id)
        request.session['viewed_videos'] = viewed_videos
    
    # For related videos, apply same visibility logic
    related_videos = Video.objects.filter(
        category=video.category,
        is_active=True
    ).exclude(pk=video.pk)
    
    if request.user.is_authenticated:
        if not request.user.is_superuser:
            from django.db.models import Q
            related_videos = related_videos.filter(
                Q(visibility='public') | 
                Q(visibility='private', added_by=request.user)
            )
    else:
        related_videos = related_videos.filter(visibility='public')
        
    related_videos = related_videos[:4]
    
    return render(request, 'core/video_detail.html', {
        'video': video,
        'related_videos': related_videos,
    })


