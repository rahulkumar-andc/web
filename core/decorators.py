from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: False)(view_func)(request, *args, **kwargs)
            
            if request.user.role in allowed_roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check hierarchy
            if 'super_admin' in allowed_roles and request.user.is_super_admin():
                return view_func(request, *args, **kwargs)
            if 'admin' in allowed_roles and request.user.is_admin_role():
                return view_func(request, *args, **kwargs)
            if 'moderator' in allowed_roles and request.user.is_moderator():
                return view_func(request, *args, **kwargs)
            if 'contributor' in allowed_roles and request.user.is_contributor():
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied
        return _wrapped_view
    return decorator

def contributor_required(view_func):
    return role_required(['contributor', 'moderator', 'admin', 'super_admin'])(view_func)

def moderator_required(view_func):
    return role_required(['moderator', 'admin', 'super_admin'])(view_func)

def admin_required(view_func):
    return role_required(['admin', 'super_admin'])(view_func)

def super_admin_required(view_func):
    return role_required(['super_admin'])(view_func)
