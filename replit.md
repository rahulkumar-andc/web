# VillenSec - Django Tools Platform

## Overview
VillenSec is a Django-based web platform for managing tools with a premium access system. Users can browse tools, request premium access, and submit reviews.

## Project Architecture

### Tech Stack
- **Backend**: Django 5.2.1
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: django-allauth with Google/GitHub OAuth
- **Rich Text Editor**: CKEditor 5
- **Static Files**: WhiteNoise
- **Styling**: Custom CSS with animations

### Apps Structure
- **core**: Main app with CustomUser model, blog posts, services, contacts
- **tools**: Tools management with premium access and reviews

### Key Models
- `CustomUser`: Extended user model with profile fields (bio, premium status, social links)
- `BlogPost`: Blog content with CKEditor rich text
- `Tool`: Tool entries with categories, videos, and source code links
- `PremiumRequest`: User requests for premium access
- `ToolReview`: User ratings and reviews for tools
- `Service`: Service listings with categories
- `OTP`: One-time passwords for email verification

## Running the Project

### Development Server
```bash
python manage.py runserver 0.0.0.0:5000
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static Files
```bash
python manage.py collectstatic
```

### Create Superuser
```bash
python manage.py createsuperuser
```

## Environment Variables
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: PostgreSQL connection URL (optional, defaults to SQLite)
- `EMAIL_HOST_USER`: SMTP email address
- `EMAIL_HOST_PASSWORD`: SMTP email password
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth secret
- `GITHUB_CLIENT_ID`: GitHub OAuth client ID
- `GITHUB_CLIENT_SECRET`: GitHub OAuth secret

## Recent Changes
- **December 2, 2025 (Replit Environment Setup)**:
  - **Environment Configuration**:
    - Installed Python 3.11 and all project dependencies
    - Configured Django to accept all hosts (ALLOWED_HOSTS = ['*']) for Replit proxy
    - Applied all database migrations (using SQLite for development)
    - Collected static files (220 files)
    - Set up workflow to run Django development server on port 5000
    - Configured deployment settings for Replit autoscale deployment
  - **Workflow Setup**:
    - Django Server: `python manage.py runserver 0.0.0.0:5000`
    - Output type: webview on port 5000
  - **Deployment Configuration**:
    - Build command: `python manage.py collectstatic --noinput`
    - Run command: `gunicorn --bind=0.0.0.0:5000 --reuse-port --workers=2 --threads=2 villen.wsgi:application`
    - Deployment target: autoscale (for cost-efficient web hosting)
  - **Status**: Application is running successfully in Replit environment

- **November 28, 2025 (UI Update)**:
  - **User Profile Dropdown**:
    - Added user profile photo in header (top right corner) after login
    - Shows first letter avatar if no profile picture uploaded
    - Dropdown menu with "Profile Settings" and "Logout" options
    - Online indicator with pulse animation
    - Cyberpunk/neon styling matching existing theme
    - Full accessibility support with aria-labels
    - Styled Register button with neon gradient for non-authenticated users

- **November 28, 2025 (Security Update)**:
  - **Security Hardening**:
    - Removed hardcoded reCAPTCHA keys (now environment variables)
    - Added custom PasswordStrengthValidator (requires uppercase, lowercase, digit, special char)
    - Increased minimum password length to 10 characters
    - Added Bleach library for HTML sanitization
    - Added URL validation to prevent XSS via malicious URLs
    - Added phone number validation
    - Added username validation with length and character restrictions
  - **Enhanced Security Headers**:
    - Added X-XSS-Protection header
    - Added Cross-Origin-Opener-Policy header
    - Added Cross-Origin-Resource-Policy header
    - Added X-Permitted-Cross-Domain-Policies header
    - Improved Permissions-Policy (added payment, usb restrictions)
    - Added Cache-Control headers for sensitive pages
    - Enhanced CSP for reCAPTCHA support
  - **Input Sanitization**:
    - All form inputs now sanitized with Bleach
    - CKEditor content sanitized with allowlist approach
    - URL fields validated for dangerous patterns (javascript:, data:, etc.)
  - **Suspicious Activity Detection**:
    - Expanded SQL injection patterns (40+ patterns)
    - Added XSS pattern detection
    - Added HTML injection patterns
    - Added time-based attack patterns
  - **Session Security**:
    - SESSION_COOKIE_HTTPONLY enabled in development
    - SESSION_COOKIE_SAMESITE set to Lax
    - CSRF_COOKIE_SAMESITE set to Lax

- **November 27, 2025 (Update 2)**: 
  - **Premium Access System Improvements**:
    - Added Premium Tiers: Basic, Pro, Enterprise
    - Added premium duration tracking (30 days, 90 days, 6 months, 1 year, lifetime)
    - Added premium expiry with automatic status update
    - Added PremiumHistory model for audit trail
    - Admin can approve with custom tier/duration
    - Admin can revoke premium with reason
    - Premium users page for management
    - Enhanced request form with tier selection
    - Better status page with remaining days
  - **Security Enhancements v2**:
    - Added SecurityHeadersMiddleware (CSP, X-Content-Type-Options, Permissions-Policy)
    - Added SessionSecurityMiddleware for session tracking
    - Added SuspiciousActivityMiddleware for detecting malicious patterns
    - Added UserSession model for active session management
    - Users can view all active sessions
    - Users can terminate individual sessions
    - Users can logout from all devices
    - New device login detection and logging
    - Enhanced SecurityLog with more action types
  - **Admin Dashboard Updates**:
    - Stats cards for users, premium, requests, tools
    - Modal-based approve/reject with tier selection
    - Premium users management page
    - Revoke premium functionality

- **November 27, 2025 (Update 1)**: 
  - Migrated from Django default User to CustomUser model
  - Combined UserProfile fields into CustomUser
  - Configured for Replit environment (ALLOWED_HOSTS, CSRF, CORS)
  - Fresh database migrations with new user model
  - Added OTP rate limiting (5 attempts, 30 min lockout)
  - Added login rate limiting with django-axes (5 attempts)
  - Added registration rate limiting (5/hour per IP)
  - Added contact form rate limiting (10/min)
  - Created security logging system (SecurityLog, OTPAttemptLog, LoginAttemptLog)
  - Added production security settings (HSTS, secure cookies, XSS protection)
  - Improved premium access workflow with audit logging

### New Models (Update 2)
- `PremiumHistory`: Tracks all premium status changes (activated, upgraded, revoked, expired)
- `UserSession`: Tracks active user sessions with device info

### Security Models
- `OTP`: Enhanced with attempt tracking and lockout
- `OTPAttemptLog`: Tracks all OTP verification attempts
- `LoginAttemptLog`: Tracks login attempts
- `SecurityLog`: Comprehensive security event logging (25+ action types)

### Security Middleware
- `SecurityHeadersMiddleware`: CSP, X-Frame-Options, Permissions-Policy
- `SessionSecurityMiddleware`: Session tracking, premium expiry check
- `SuspiciousActivityMiddleware`: Detects SQL injection, XSS patterns

### Security Features
- Rate limiting on registration, OTP verification, login
- Automatic account lockout after failed attempts
- IP-based throttling
- Security event logging for admin monitoring
- Production-ready HTTPS/cookie security settings
- Active session management with logout all devices
- New device login alerts
- Suspicious activity detection

## User Preferences
- No emojis in code unless requested
- Hindi comments preserved in code

## Deployment
- Uses gunicorn for production server
- WhiteNoise for static file serving
- Configure DATABASE_URL for PostgreSQL in production
- Set `PRODUCTION=true` environment variable for production security settings

### Production Readiness (November 28, 2025)
- **Settings Updated**: SECRET_KEY is now required in production (raises error if missing)
- **DEBUG Mode**: Automatically disabled when PRODUCTION=true
- **Security Headers**: Full production security headers enabled
- **ALLOWED_HOSTS**: Configured for Replit domains and custom domain (villen.me)
- **Static Files**: Collected and served via WhiteNoise with compression
- **Deployment Configuration**: 
  - Build: Installs dependencies, runs migrations, collects static files
  - Run: Gunicorn with 2 workers and 2 threads
  - Target: Autoscale deployment for cost efficiency
- **Cookie Security**: SameSite=Lax in production (compatible with OAuth flows)

### Required Secrets for Production
- `SECRET_KEY` (required): Django secret key - must be a long random string
- `PRODUCTION` (set in production env): Set to "true" to enable production mode
- `DATABASE_URL` (optional): PostgreSQL connection string

### Optional Secrets
- `EMAIL_HOST_USER`: SMTP email for notifications
- `EMAIL_HOST_PASSWORD`: SMTP password
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Google OAuth
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET`: GitHub OAuth
