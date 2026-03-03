# herald_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def root(request):
    return JsonResponse({
        'name': 'Herald Backend API',
        'status': 'ok',
        'base_path': '/api/v1/',
        'auth_signup': '/api/v1/auth/signup/',
        'auth_signin': '/api/v1/auth/signin/',
    })


def health(request):
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    path('', root, name='root'),
    path('health/', health, name='health'),
    path('admin/', admin.site.urls),
    
    # JWT endpoints (legacy)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # New v1 API endpoints
    path('api/', include('core.urls')),
    
    # API Auth (browsable API)
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)