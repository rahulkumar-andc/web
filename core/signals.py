from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from axes.signals import user_locked_out
from .models import SecurityLog, LoginAttemptLog, UserSession
from .alerts import send_security_email, send_admin_alert
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    if request is None:
        return '0.0.0.0'
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    
    # Check for New IP
    # We look for previous successful logins from this user with a different IP
    # But wait, we need to check if *this* IP has been seen before.
    # If it hasn't, it's a new IP.
    
    previous_sessions = UserSession.objects.filter(user=user, ip_address=ip_address).exists()
    # Also check SecurityLog for past logins
    previous_logs = SecurityLog.objects.filter(user=user, action='login_success', ip_address=ip_address).exists()
    
    is_new_ip = not (previous_sessions or previous_logs)
    
    LoginAttemptLog.objects.create(
        username=user.username,
        ip_address=ip_address,
        was_successful=True,
        user_agent=user_agent
    )
    
    SecurityLog.objects.create(
        user=user,
        action='login_success',
        ip_address=ip_address,
        user_agent=user_agent,
        details={'method': 'standard', 'is_new_ip': is_new_ip}
    )
    
    if hasattr(user, 'reset_login_attempts'):
        user.reset_login_attempts()
    
    logger.info(f"User {user.username} logged in from {ip_address}")
    
    if is_new_ip:
        try:
            send_security_email(
                user,
                "New IP Login Detected",
                f"We detected a login from a new IP address: {ip_address}",
                {'ip': ip_address, 'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')}
            )
        except Exception as e:
            pass


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip_address = get_client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    username = credentials.get('username', 'unknown')
    
    LoginAttemptLog.objects.create(
        username=username,
        ip_address=ip_address,
        was_successful=False,
        user_agent=user_agent
    )
    
    SecurityLog.objects.create(
        user=None,
        action='login_failed',
        ip_address=ip_address,
        user_agent=user_agent,
        details={'username': username}
    )
    
    logger.warning(f"Failed login attempt for {username} from {ip_address}")


@receiver(user_locked_out)
def log_user_locked_out(sender, request, username, ip_address, **kwargs):
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
    ip = ip_address or get_client_ip(request)
    
    SecurityLog.objects.create(
        user=None,
        action='login_locked',
        ip_address=ip,
        user_agent=user_agent,
        details={'username': username, 'reason': 'axes_lockout'}
    )
    
    logger.warning(f"User {username} locked out from {ip}")
    
    # Alert Admin
    send_admin_alert(
        "User Account Locked Out",
        f"User account '{username}' has been locked out due to excessive failed attempts.",
        details={'Username': username, 'IP': ip}
    )
    
    # Try to find user to alert them
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
        send_security_email(
            user,
            "Account Locked",
            "Your account has been temporarily locked due to multiple failed login attempts.",
            details={'IP': ip}
        )
    except User.DoesNotExist:
        pass


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user and user.is_authenticated:
        ip_address = get_client_ip(request)
        
        SecurityLog.objects.create(
            user=user,
            action='logout',
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
            details={}
        )
        
        logger.info(f"User {user.username} logged out from {ip_address}")
