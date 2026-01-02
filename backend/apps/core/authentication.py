"""Auth0 JWT Authentication for Django REST Framework"""
import jwt
import requests
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import User


class DevAuthentication(authentication.BaseAuthentication):
    """
    Development authentication - automatically authenticates as test user.
    DO NOT USE IN PRODUCTION!
    """
    
    def authenticate(self, request):
        # Get or create the test user
        try:
            user = User.objects.get(email='test@nairatrack.com')
        except User.DoesNotExist:
            # Create test user if it doesn't exist
            user = User.objects.create_user(
                email='test@nairatrack.com',
                username='testuser',
                password='testpassword123',
                first_name='Test',
                last_name='User',
                currency='NGN',
                timezone='Africa/Lagos',
            )
        
        return (user, None)


class Auth0JWTAuthentication(authentication.BaseAuthentication):
    """Authenticate requests using Auth0 JWT tokens"""
    
    def __init__(self):
        self.jwks_client = None
    
    def get_jwks_client(self):
        if not self.jwks_client:
            jwks_url = f'https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json'
            self.jwks_client = jwt.PyJWKClient(jwks_url)
        return self.jwks_client
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header[7:]
        
        try:
            jwks_client = self.get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=settings.AUTH0_ALGORITHMS,
                audience=settings.AUTH0_API_AUDIENCE,
                issuer=f'https://{settings.AUTH0_DOMAIN}/'
            )
            
            auth0_id = payload.get('sub')
            email = payload.get('email', '')
            
            user, created = User.objects.get_or_create(
                auth0_id=auth0_id,
                defaults={
                    'email': email,
                    'username': email or auth0_id,
                    'first_name': payload.get('given_name', ''),
                    'last_name': payload.get('family_name', ''),
                }
            )
            
            if not created and email and user.email != email:
                user.email = email
                user.save(update_fields=['email'])

            if created and settings.DEBUG:
                # Seed data for new users ONLY IN DEBUG/DEV MODE
                try:
                    from apps.core.management.commands.seed_data import Command as SeedCommand
                    cmd = SeedCommand()
                    cmd.stdout = open('/dev/null', 'w')  # Verify stdout exists
                    
                    # Create system categories if they don't exist
                    cmd.create_categories(user)
                    
                    # Create existing data
                    accounts = cmd.create_accounts(user)
                    cmd.create_transactions(user, accounts)
                    cmd.create_budgets(user)
                    cmd.create_goals(user)
                    cmd.create_recurring(user, accounts)
                except Exception as e:
                    print(f"Failed to seed data for user {user.id}: {str(e)}")
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')
