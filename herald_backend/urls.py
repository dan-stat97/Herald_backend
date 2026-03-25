# herald_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connection
from core.admin_views import AdminDashboardView, DBTestView


def root(request):
    return JsonResponse({
        'name': 'Herald Backend API',
        'status': 'ok',
        'base_path': '/api/v1/',
        'auth_signup': '/api/v1/auth/signup/',
        'auth_signin': '/api/v1/auth/signin/',
    })


def health(request):
    """Health check with database connectivity test"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return JsonResponse({
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'database': db_status
    })


urlpatterns = [
    path('', root, name='root'),
    path('health/', health, name='health'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/db-test/', DBTestView.as_view(), name='admin_db_test'),
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