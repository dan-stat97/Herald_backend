
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignupView, SigninView, SignoutView, RefreshView, CurrentUserView, UserProfileViewSet


router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('signup/', SignupView.as_view(), name='auth-signup'),
    path('signin/', SigninView.as_view(), name='auth-signin'),
    path('signout/', SignoutView.as_view(), name='auth-signout'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('user/', CurrentUserView.as_view(), name='auth-user'),
    path('users/', include(router.urls)),
]