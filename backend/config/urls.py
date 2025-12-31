"""URL Configuration for NairaTrack API"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/health', health_check),
    path('api/v1/', include('apps.core.urls')),
]
