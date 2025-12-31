"""Development settings"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='nairatrack'),
        'USER': config('DB_USER', default='nairatrack'),
        'PASSWORD': config('DB_PASSWORD', default='nairatrack'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Allow all CORS in development
CORS_ALLOW_ALL_ORIGINS = True

# Mono Sandbox Keys (for development)
MONO_PUBLIC_KEY = config('MONO_PUBLIC_KEY', default='test_pk_p8ytbx827qwqxk6mdu53')
MONO_SECRET_KEY = config('MONO_SECRET_KEY', default='test_sk_kaemd5grhs5tke3n2o2s')

# Development Authentication - Use simple session auth for testing
# Set DEV_AUTH_BYPASS=true to bypass Auth0 and use test user
DEV_AUTH_BYPASS = config('DEV_AUTH_BYPASS', default='true', cast=bool)

if DEV_AUTH_BYPASS:
    REST_FRAMEWORK = {
        **REST_FRAMEWORK,
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'apps.core.authentication.DevAuthentication',
        ],
    }
