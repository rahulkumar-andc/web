
import os
import pytest
from django.conf import settings
from django.test import RequestFactory
from core.utils import get_client_ip

def test_allowed_hosts_default():
    # Since we didn't set ALLOWED_HOSTS env var in the test runner, it should be ['*']
    # Note: settings are loaded once, so this reflects the state when pytest started.
    assert '*' in settings.ALLOWED_HOSTS

def test_get_client_ip_cloudflare():
    factory = RequestFactory()
    request = factory.get('/')
    request.META['HTTP_CF_CONNECTING_IP'] = '1.2.3.4'
    request.META['HTTP_X_FORWARDED_FOR'] = '5.6.7.8'
    
    ip = get_client_ip(request)
    assert ip == '1.2.3.4'

def test_get_client_ip_x_forwarded_for():
    factory = RequestFactory()
    request = factory.get('/')
    request.META['HTTP_X_FORWARDED_FOR'] = '5.6.7.8, 9.10.11.12'
    
    ip = get_client_ip(request)
    assert ip == '5.6.7.8'

def test_get_client_ip_real_ip():
    factory = RequestFactory()
    request = factory.get('/')
    request.META['HTTP_X_REAL_IP'] = '10.11.12.13'
    
    ip = get_client_ip(request)
    assert ip == '10.11.12.13'

def test_get_client_ip_remote_addr():
    factory = RequestFactory()
    request = factory.get('/')
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    
    ip = get_client_ip(request)
    assert ip == '127.0.0.1'
