"""
Production settings for Villen Django project.

- DEBUG set to False
- ALLOWED_HOSTS configured
- Static files handling for production
- Security settings for cookies and CSRF
- Deployment instructions for Heroku and DigitalOcean

Note: Adjust ALLOWED_HOSTS and email settings as needed.
"""

from .settings import *

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourdomain.com', 'www.yourdomain.com', 'your-heroku-app.herokuapp.com']

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# Additional static files dirs if any
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Security settings
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Email settings (update for production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.your-email-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Deployment instructions:

"""
Heroku Deployment:
- Install Heroku CLI
- Create a Heroku app: heroku create your-app-name
- Add Heroku Postgres addon: heroku addons:create heroku-postgresql:hobby-dev
- Set environment variables for SECRET_KEY, DEBUG, ALLOWED_HOSTS, EMAIL settings
- Use gunicorn as WSGI server
- Collect static files: python manage.py collectstatic
- Push code to Heroku: git push heroku main
- Run migrations: heroku run python manage.py migrate

DigitalOcean Deployment:
- Set up a Droplet with Ubuntu
- Install Python, pip, virtualenv, PostgreSQL, Nginx, Gunicorn
- Clone your project repo
- Set up virtualenv and install requirements
- Configure PostgreSQL database and user
- Configure Gunicorn systemd service
- Configure Nginx as reverse proxy
- Set environment variables for production settings
- Collect static files
- Run migrations
- Start Gunicorn and Nginx services
"""
