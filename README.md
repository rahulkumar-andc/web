# VillenSec - Cybersecurity Tools Platform

## Overview
VillenSec is a Django-based cybersecurity and tools platform featuring a premium access system, blog functionality, and comprehensive security features. Users can browse tools, request premium access, submit reviews, and engage with blog content.

## Key Features

### Tool Management
- Create, update, delete, and list tools with rich content (CKEditor 5)
- Support for images, videos, and source code links
- Category-based organization

### Premium Access System
- Multi-tier premium levels: Basic, Pro, Enterprise
- Flexible duration options: 30, 90, 180, 365 days, or lifetime
- Premium request workflow with admin approval/rejection
- Automatic expiration tracking and status updates
- Premium history audit trail

### User Features
- User registration with OTP email verification
- Social login (Google, GitHub)
- Profile management with social links
- Premium users can submit ratings and reviews for tools
- Active session management with logout from all devices

### Blog System
- Rich content blog posts with CKEditor 5
- Privacy controls for blog content

### Notes System
- Secure personal note-taking
- File attachment support
- Private and public notes options

### Admin Dashboard
- Custom admin panel at `/panel/`
- User management (active/staff toggle, delete)
- Premium request management (approve/reject with tier/duration)
- Premium users management (extend/revoke access)
- Tool and blog CRUD operations
- Security logs and login attempt monitoring
- Active session management

### Role-Based Access Control (RBAC)
- **Viewer**: Read-only access to tools and blogs.
- **Contributor**: Can create/edit own tools (requires approval).
- **Moderator**: Can approve/reject tools and manage content.
- **Admin**: Full system access.

### Web Application Firewall (WAF)
- **SQL Injection Protection**: Regex-based detection of SQLi patterns.
- **XSS Protection**: Filters malicious scripts in requests.
- **IP Reputation**: Integration with AbuseIPDB to block malicious IPs.
- **Honeypots**: Traps for bots accessing suspicious paths (e.g., `/wp-admin/`).
- **CSP Reporter**: Endpoint to log Content Security Policy violations.

### Analytics & Monitoring
- **Dashboard**: Visual metrics for Daily Active Users (DAU), Downloads, and Revenue.
- **Device Map**: Real-time geolocation map of active users.
- **Security Alerts**: Automated email/SMS notifications for:
    - New IP/Device logins
    - Account lockouts
    - High-severity WAF events
- **Charts**: Failed login attempts and tool popularity.

### Security Features
- **Two-Factor Authentication (2FA)**: TOTP-based 2FA for enhanced account security.
- OTP rate limiting (5 attempts, 30 min lockout)
- Login rate limiting with django-axes (5 attempts)
- Registration rate limiting (5/hour per IP)
- Security headers (CSP, X-Frame-Options, HSTS)
- Session security middleware
- Suspicious activity detection (SQL injection, XSS patterns)
- Comprehensive security logging

## Tech Stack
- **Backend**: Django 5.2.1
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: django-allauth with Google/GitHub OAuth
- **Rich Text Editor**: CKEditor 5
- **Static Files**: WhiteNoise
- **Server**: Gunicorn
- **Styling**: Custom CSS with cyberpunk/hacker aesthetic
- **Testing**: pytest, factory_boy

## Project Structure
```
web/
├── core/                 # Main app (users, blog, services, contacts, notes)
│   ├── models.py         # CustomUser, BlogPost, Service, OTP, SecurityLog, Note
│   ├── views.py          # Authentication, blog, profile, notes views
│   ├── middleware.py     # Security headers, session tracking, WAF
│   └── templates/        # Core templates
├── tools/                # Tools and premium access
│   ├── models.py         # Tool, PremiumRequest, ToolReview
│   └── templates/        # Tool templates
├── custom_admin/         # Custom admin dashboard
│   └── templates/        # Admin panel templates
├── static/               # CSS, JS, images
├── media/                # Uploaded files
├── villen/               # Django project settings
│   ├── settings.py       # Main settings
│   └── urls.py           # URL configuration
├── requirements.txt      # Python dependencies
└── manage.py             # Django management script
```

## Environment Variables

### Required (Production)
- `SECRET_KEY`: Django secret key (required in production)
- `PRODUCTION`: Set to "true" for production mode

### Database
- `DATABASE_URL`: PostgreSQL connection string

### Email (for OTP and notifications)
- `EMAIL_HOST_USER`: SMTP email address
- `EMAIL_HOST_PASSWORD`: SMTP password

### OAuth (optional)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth secret
- `GITHUB_CLIENT_ID`: GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth secret

## Installation

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Run development server
python manage.py runserver 0.0.0.0:5000
```

### Production
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --run-syncdb

# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 villen.wsgi:application
```

## Testing

Run the comprehensive test suite using `pytest`:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.

# Run specific test file
pytest core/tests/test_auth.py
```

## URL Structure
- `/` - Home page
- `/about/` - About page
- `/blog/` - Blog listing
- `/contact/` - Contact form
- `/tools/` - Tools listing
- `/accounts/` - Authentication (login, register, social)
- `/panel/` - Custom admin dashboard (staff only)
- `/admin/` - Django admin

## Security
- All passwords hashed with Django's default hasher
- CSRF protection enabled
- Secure cookies in production
- HTTPS enforced in production
- Rate limiting on sensitive endpoints
- Security event logging

## License
All rights reserved.

## Contact
For support or inquiries, contact Villen.
