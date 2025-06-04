"""
Production settings for Villen Django project.

- DEBUG set to False for safety
- Allowed hosts configured properly
- Static & media file serving optimized
- Security tightened on cookies, CSRF, headers
"""

from .settings import *

DEBUG = False

ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    'villen.me', 
    'www.villen.me', 
    'web-soz1.onrender.com'  # Add your Heroku or DigitalOcean domains here
]

# Static files - collected by collectstatic for production serving
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Optional extra static directories (if needed)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files - same as dev
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security best practices for production
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email settings for production (update with your provider)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.your-email-provider.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your-email@example.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'your-email-password')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Additional production tips:
# - Make sure to set environment variables for all secrets
# - Use HTTPS everywhere (nginx, heroku settings)
# - Run `python manage.py collectstatic` before deploying
# - Run migrations after deployment

# Optional: HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
