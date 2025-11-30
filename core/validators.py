import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordStrengthValidator:
    def __init__(self, min_length=10):
        self.min_length = min_length

    def validate(self, password, user=None):
        errors = []
        
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))
        
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))
        
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one digit."))
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
            errors.append(_("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."))
        
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character."
        )


def validate_safe_url(value):
    if not value:
        return value
    
    value = value.strip()
    
    dangerous_patterns = [
        r'javascript:',
        r'data:',
        r'vbscript:',
        r'file:',
        r'<script',
        r'onclick',
        r'onerror',
        r'onload',
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if pattern in value_lower:
            raise ValidationError(_("URL contains potentially unsafe content."))
    
    if not value.startswith(('http://', 'https://', '/')):
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', value):
            raise ValidationError(_("URL must start with http://, https://, or be a relative path."))
    
    return value


def validate_phone_number(value):
    if not value:
        return value
    
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', value)
    
    if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
        raise ValidationError(
            _("Enter a valid phone number. It should contain 7-15 digits and may start with +.")
        )
    
    return value


ALLOWED_EMBED_HOSTS = [
    'www.youtube.com',
    'youtube.com',
    'player.vimeo.com',
    'vimeo.com',
]


def _validate_url_host(url, allowed_hosts):
    import re
    if not url:
        return False
    url_lower = url.lower().strip()
    pattern = r'^https?://([^/]+)'
    match = re.match(pattern, url_lower)
    if not match:
        return False
    host = match.group(1)
    return any(host == allowed or host.endswith('.' + allowed) for allowed in allowed_hosts)


def _filter_src_attr(tag, name, value):
    if tag == 'img':
        if name == 'src':
            value_lower = value.lower().strip()
            if value_lower.startswith('data:image/'):
                return True
            if value_lower.startswith(('http://', 'https://')):
                return True
            return False
        return name in ['alt', 'width', 'height', 'loading']
    if tag == 'a':
        if name == 'href':
            value_lower = value.lower().strip()
            if value_lower.startswith(('javascript:', 'data:', 'vbscript:')):
                return False
            return True
        if name == 'rel':
            return True
        return name in ['title', 'target']
    return True


def sanitize_html(content, allowed_tags=None, allowed_attrs=None):
    import bleach
    
    if allowed_tags is None:
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'ul', 'ol', 'li', 'blockquote', 'pre', 'code', 'a', 'img', 'table',
            'thead', 'tbody', 'tr', 'th', 'td', 'figure', 'figcaption'
        ]
    
    if allowed_attrs is None:
        allowed_attrs = {
            'a': _filter_src_attr,
            'img': _filter_src_attr,
            'td': ['colspan', 'rowspan'],
            'th': ['colspan', 'rowspan', 'scope'],
            'blockquote': ['cite'],
            'pre': ['class'],
            'code': ['class'],
        }
    
    cleaned = bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    
    return cleaned
