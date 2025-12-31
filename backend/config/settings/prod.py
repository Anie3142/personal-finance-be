"""Production settings"""
from .base import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',')])

DATABASES = {
    'default': dj_database_url.config(default=config('DATABASE_URL', default=''))
}

# Disable SSL redirect since Cloudflare handles HTTPS termination
# The traffic from Cloudflare tunnel -> Traefik -> Django is HTTP internally
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
