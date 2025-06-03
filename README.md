# Villen Django Project

## Overview
Villen is a Django-based web application featuring user profiles, blog posts, contact forms with reCAPTCHA, and more. This project is configured for both development and production environments.

## Features
- User registration and authentication
- User profile management with image uploads
- Blog post creation, editing, and deletion (admin/superuser only)
- Contact form with AJAX and Google reCAPTCHA validation
- Custom 404 and 500 error pages
- Static and media files handling
- Security hardening for production

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip
- virtualenv (recommended)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd villen
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser (admin):
   ```
   python manage.py createsuperuser
   ```

6. Collect static files (for production):
   ```
   python manage.py collectstatic
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

### Environment Settings
- Use `villen/settings.py` for development (DEBUG=True).
- Use `villen/settings_production.py` for production (DEBUG=False).
- Update `ALLOWED_HOSTS` in `settings_production.py` as needed.

## Running Tests
(To be added if tests are implemented)

## Deployment
Refer to the deployment instructions in `villen/settings_production.py` for Heroku and DigitalOcean.

## Credits
- Developed by [Your Name]
- Uses Django, Pillow, django-ckeditor, django-recaptcha, and other open-source packages.

## License
Specify your project license here.
