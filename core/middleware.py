# Security middleware
# core/middleware.py
import hashlib
import logging
from django.conf import settings
from django.utils import timezone
from django.contrib.sessions.models import Session

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
        response['X-XSS-Protection'] = '1; mode=block'
        response['X-Permitted-Cross-Domain-Policies'] = 'none'
        response['Cross-Origin-Opener-Policy'] = 'same-origin'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        
        if getattr(settings, 'IS_PRODUCTION', False):
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.ckeditor.com https://code.jquery.com https://www.google.com https://www.gstatic.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.ckeditor.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "frame-src https://www.google.com https://www.youtube.com https://player.vimeo.com; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests; "
                "report-uri /core/csp-report/;"
            )
            response['Content-Security-Policy'] = csp
        
        return response


class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._request_count = 0
        self._prune_interval = 100

    def __call__(self, request):
        if request.user.is_authenticated:
            self._check_premium_expiry(request)
            self._track_session_limited(request)
        
        response = self.get_response(request)
        return response
    
    def _track_session_limited(self, request):
        from .models import UserSession
        from django.core.cache import cache
        
        session_key = request.session.session_key
        if not session_key:
            return
        
        cache_key = f'session_tracked_{session_key}'
        if cache.get(cache_key):
            return
        
        cache.set(cache_key, True, 300)
        
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        try:
            user_session, created = UserSession.objects.update_or_create(
                session_key=session_key,
                user=request.user,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'last_activity': timezone.now(),
                }
            )
            
            if created:
                user_session.parse_user_agent()
                user_session.save()
                self._check_new_device(request, user_session)
                self._prune_old_sessions(request.user)
                
        except Exception as e:
            logger.warning(f"Failed to track session: {e}")
    
    def _prune_old_sessions(self, user):
        from .models import UserSession
        from datetime import timedelta
        
        cutoff = timezone.now() - timedelta(days=30)
        UserSession.objects.filter(
            user=user,
            last_activity__lt=cutoff
        ).delete()
        
        max_sessions = 10
        user_sessions = UserSession.objects.filter(user=user).order_by('-last_activity')
        if user_sessions.count() > max_sessions:
            old_sessions = user_sessions[max_sessions:]
            for s in old_sessions:
                s.delete()
    
    def _check_new_device(self, request, session):
        from .models import UserSession, SecurityLog
        from .alerts import send_security_email
        
        existing_sessions = UserSession.objects.filter(
            user=request.user
        ).exclude(session_key=session.session_key)
        
        if existing_sessions.exists():
            known_fingerprints = set()
            for s in existing_sessions:
                fingerprint = f"{s.device_type}_{s.browser}_{s.os}"
                known_fingerprints.add(fingerprint)
            
            current_fingerprint = f"{session.device_type}_{session.browser}_{session.os}"
            
            if current_fingerprint not in known_fingerprints:
                SecurityLog.objects.create(
                    user=request.user,
                    action='new_device_login',
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    details={
                        'device_type': session.device_type,
                        'browser': session.browser,
                        'os': session.os,
                    }
                )
                
                send_security_email(
                    request.user,
                    "New Device Login Detected",
                    f"We detected a login from a new device: {session.device_type} running {session.os} on {session.browser}.",
                    details={
                        'Device': session.device_type,
                        'OS': session.os,
                        'Browser': session.browser,
                        'IP': session.ip_address
                    }
                )
    
    def _check_premium_expiry(self, request):
        from .models import SecurityLog, PremiumHistory
        from django.core.cache import cache
        
        user = request.user
        if not user.is_premium:
            return
        
        cache_key = f'premium_check_{user.id}'
        if cache.get(cache_key):
            return
        cache.set(cache_key, True, 60)
        
        if user.premium_expires_at and user.premium_expires_at <= timezone.now():
            previous_tier = user.premium_tier
            previous_expiry = user.premium_expires_at
            
            user.is_premium = False
            user.premium_request_status = 'expired'
            user.premium_tier = 'none'
            user.premium_expires_at = None
            user.save(update_fields=['is_premium', 'premium_request_status', 'premium_tier', 'premium_expires_at'])
            
            SecurityLog.objects.create(
                user=user,
                action='premium_expired',
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                details={'previous_tier': previous_tier}
            )
            
            PremiumHistory.objects.create(
                user=user,
                action='expired',
                previous_tier=previous_tier,
                new_tier='none',
                previous_expiry=previous_expiry,
            )
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class WAFMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.waf_enabled = getattr(settings, 'WAF_ENABLED', True)
        self.abuseipdb_key = getattr(settings, 'ABUSEIPDB_API_KEY', '')
        
        self.sqli_patterns = [
            r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
            r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
            r"((\%27)|(\'))union",
            r"exec(\s|\+)+(s|x)p\w+",
            r"union(\s|\+)+select",
            r"information_schema",
            r"waitfor(\s|\+)+delay",
            r"benchmark\(",
            r"sleep\(",
            r"pg_sleep\(",
            r"drop(\s|\+)+table",
            r"delete(\s|\+)+from",
            r"truncate(\s|\+)+table",
            r"update(\s|\+)+.*set",
            r"insert(\s|\+)+into",
            r"select(\s|\+)+.*from",
            r"1\s*=\s*1",
            r"or\s+1\s*=\s*1",
            r"admin'--",
        ]
        
        self.xss_patterns = [
            r"<script",
            r"javascript:",
            r"vbscript:",
            r"expression\(",
            r"onload=",
            r"onerror=",
            r"onclick=",
            r"onmouseover=",
            r"onfocus=",
            r"onblur=",
            r"<iframe",
            r"<object",
            r"<embed",
            r"<svg",
            r"<img.*src=",
            r"document\.cookie",
            r"document\.domain",
            r"document\.write",
        ]
        
        self.honeypot_paths = [
            '/wp-admin/',
            '/administrator/',
            '/phpmyadmin/',
            '/admin-login/',
            '/login.php',
            '/wp-login.php',
            '/.env',
            '/config.php',
        ]
        
        self.excluded_paths = [
            '/panel/', # Custom admin
            '/admin/', # Django admin
            '/ckeditor/',
            '/blog/', # Blog content might have some HTML
        ]
        
        import re
        self.sqli_regex = [re.compile(p, re.IGNORECASE) for p in self.sqli_patterns]
        self.xss_regex = [re.compile(p, re.IGNORECASE) for p in self.xss_patterns]

    def _check_reputation(self, request):
        if request.user.is_authenticated:
            if request.user.reputation_score < 0:
                return self._block_request(request, "Account locked due to low reputation.")
        return None

    def __call__(self, request):
        if not self.waf_enabled:
            return self.get_response(request)
            
        # Check Reputation
        blocked = self._check_reputation(request)
        if blocked:
            return blocked

        # Check IP Reputation
        blocked = self._check_ip_reputation(request)
        if blocked:
            return blocked
            
        # Check Honeypot
        if self._check_honeypot(request):
            self._log_waf_event(request, 'honeypot_triggered', {'message': 'Honeypot accessed'})
            return self._block_request(request, 'Suspicious activity detected')

        # Check SQLi and XSS (skip excluded paths)
        if self._should_check_content(request):
            # Check SQL Injection
            if self._check_sqli(request):
                self._log_waf_event(request, 'sqli_attempt', {'path': request.path})
                return self._block_request(request, "Access Denied: SQL Injection Detected")
            
            # Check XSS
            if self._check_xss(request):
                self._log_waf_event(request, 'xss_attempt', {'path': request.path})
                return self._block_request(request, "Access Denied: XSS Detected")
        
        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip

    def _check_ip_reputation(self, ip):
        from django.core.cache import cache
        import requests
        
        if not self.abuseipdb_key:
            return False
            
        cache_key = f'waf_ip_rep_{ip}'
        is_bad = cache.get(cache_key)
        
        if is_bad is not None:
            return is_bad
            
        # If not in cache, check API (with short timeout to not block too long)
        # In async environment this would be better, but for sync middleware we must be fast
        try:
            url = 'https://api.abuseipdb.com/api/v2/check'
            querystring = {'ipAddress': ip, 'maxAgeInDays': '90'}
            headers = {'Key': self.abuseipdb_key, 'Accept': 'application/json'}
            
            # Use very short timeout to avoid latency
            response = requests.get(url, headers=headers, params=querystring, timeout=1.0)
            
            if response.status_code == 200:
                data = response.json()
                score = data['data']['abuseConfidenceScore']
                is_bad = score > 80
                # Cache for 24 hours
                cache.set(cache_key, is_bad, 60 * 60 * 24)
                return is_bad
        except:
            # On error or timeout, fail open (allow request)
            pass
            
        return False

    def _check_honeypot(self, request):
        for path in self.honeypot_paths:
            if request.path.startswith(path):
                return True
        return False

    def _should_check_content(self, request):
        for excluded in self.excluded_paths:
            if request.path.startswith(excluded):
                return False
        return True

    def _check_sqli(self, request):
        content = self._get_request_content(request)
        for regex in self.sqli_regex:
            if regex.search(content):
                return True
        return False

    def _check_xss(self, request):
        content = self._get_request_content(request)
        for regex in self.xss_regex:
            if regex.search(content):
                return True
        return False

    def _get_request_content(self, request):
        content = []
        content.extend(request.GET.values())
        
        if request.method == 'POST' and not request.content_type.startswith('multipart'):
            content.extend(request.POST.values())
            
        return ' '.join([str(v) for v in content])

    def _log_waf_event(self, request, action, details):
        from .models import SecurityLog
        from .alerts import send_admin_alert
        
        user = getattr(request, 'user', None)
        if user and not user.is_authenticated:
            user = None
            
        try:
            SecurityLog.objects.create(
                user=user,
                action='suspicious_activity', # Using existing choice
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                details={
                    'waf_action': action,
                    **details
                }
            )
            logger.warning(f"WAF Blocked: {action} from {self._get_client_ip(request)}")
            
            # Send Admin Alert for high severity events
            if action in ['sqli_attempt', 'xss_attempt', 'honeypot_triggered']:
                send_admin_alert(
                    f"WAF Alert: {action}",
                    f"A high severity WAF event was triggered.\nAction: {action}\nIP: {self._get_client_ip(request)}",
                    details=details
                )
                
        except Exception as e:
            logger.error(f"WAF Logging Failed: {e}")

    def _block_request(self, request, reason):
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden(f"""
            <h1>403 Forbidden</h1>
            <p>{reason}</p>
            <p>Your IP: {self._get_client_ip(request)}</p>
            <p>Request ID: {hashlib.md5(str(timezone.now()).encode()).hexdigest()[:10]}</p>
        """)
