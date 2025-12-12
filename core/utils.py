
def get_client_ip(request):
    """
    Get the client IP address from the request, handling various headers
    used by CDNs and proxies.
    """
    # Cloudflare
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip
        
    # Standard X-Forwarded-For
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # The first IP is the original client IP
        return x_forwarded_for.split(',')[0].strip()
        
    # Real IP (Nginx, etc.)
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip
        
    # Fallback
    return request.META.get('REMOTE_ADDR', '0.0.0.0')
