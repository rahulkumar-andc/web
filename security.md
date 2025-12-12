# Security Architecture & Features

This document outlines the security measures implemented in the VillenSec application.

## 1. Network & Infrastructure Security

### Web Application Firewall (WAF)
- **Custom WAF Middleware**: Intercepts requests before they reach views.
- **Protection Vectors**:
  - **SQL Injection (SQLi)**: Regex-based pattern matching for common SQL injection vectors.
  - **Cross-Site Scripting (XSS)**: Blocks requests containing malicious script tags or event handlers.
  - **Honeypots**: Automatically blocks IPs accessing known vulnerability paths (e.g., `/wp-admin`, `/.env`).
- **IP Reputation**: Integrates with **AbuseIPDB** to check and block IPs with poor reputation scores (>80).

### CDN & Proxy Support
- **Robust IP Extraction**: `core.utils.get_client_ip` correctly identifies client IPs behind Cloudflare, Nginx, or other proxies.
- **Dynamic Configuration**: `ALLOWED_HOSTS` is configurable via environment variables.
- **Trusted Proxies**: `django-axes` is configured to trust Cloudflare headers (`HTTP_CF_CONNECTING_IP`) for rate limiting.

### Security Headers
Implemented via `SecurityHeadersMiddleware`:
- **HSTS**: Enforced for 1 year (`max-age=31536000`) with preloading.
- **CSP (Content Security Policy)**: Restricts script/style sources to trusted domains (Google, CDN, Self).
- **X-Frame-Options**: `DENY` to prevent clickjacking.
- **X-Content-Type-Options**: `nosniff`.
- **Referrer-Policy**: `strict-origin-when-cross-origin`.
- **Permissions-Policy**: Disables sensitive features (camera, mic, geolocation) by default.

---

## 2. Authentication & Identity

### Password Security
- **Validator**: `PasswordStrengthValidator` enforces:
  - Minimum 10 characters.
  - At least 1 Uppercase, 1 Lowercase, 1 Digit, 1 Special Character.
- **Hashing**: Standard Django PBKDF2 password hashing.

### Multi-Factor Authentication (MFA)
- **Email OTP**: 6-digit codes for account verification and critical actions.
- **TOTP (Authenticator App)**: Supported in data model (`totp_secret`) for 2FA.
- **Device Verification**: New devices trigger a mandatory OTP verification flow.

### Brute Force Protection
- **Library**: `django-axes` integration.
- **Policy**:
  - **Limit**: 5 failed attempts.
  - **Cool-off**: 30 minutes lockout.
  - **Lockout**: Locks both Username and IP address.
- **Admin**: Admin panel is also protected.

---

## 3. Session Management

### Session Security
- **Tracking**: `SessionSecurityMiddleware` logs every active session with IP, Device Type, OS, and Browser.
- **New Device Detection**: Automatically detects logins from unknown fingerprints and triggers alerts.
- **Session Pruning**: Automatically cleans up old/inactive sessions.
- **Cookie Security**:
  - `HttpOnly`: Yes (prevents JS access).
  - `Secure`: Yes (HTTPS only).
  - `SameSite`: 'Lax' (CSRF protection).

---

## 4. Application Security

### Input Sanitization
- **HTML Sanitization**: `bleach` library used to sanitize rich text content (Blog posts).
  - Whitelists safe tags (`p`, `b`, `i`, etc.).
  - Strips dangerous attributes (`onclick`, `javascript:` links).
- **URL Validation**: `validate_safe_url` prevents Open Redirects and XSS in URL fields.

### Data Protection
- **CSRF Protection**: Enabled globally. Strict `CSRF_TRUSTED_ORIGINS` check.
- **CORS**: Restricted to allowed origins in production.

---

## 5. Monitoring & Alerting

### Security Logging
- **Model**: `SecurityLog` records all security-relevant events.
- **Events Logged**:
  - Login Success/Failure
  - WAF Blocks (SQLi, XSS, Honeypot)
  - Password Changes
  - New Device Logins
  - Premium Tier Changes

### Active Alerting
- **User Alerts**:
  - **Email**: Sent on "New Device Login" and "Password Change".
  - **SMS**: Mock implementation for critical alerts.
- **Admin Alerts**:
  - High-severity WAF events (SQLi/XSS attempts) trigger immediate admin emails.
