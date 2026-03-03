
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView, SigninView, SignoutView, RefreshView, CurrentUserView, 
    UserProfileViewSet, SessionView, ChangePasswordView, UserPostsView, UserTasksView
)


router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('signup/', SignupView.as_view(), name='auth-signup'),
    path('signin/', SigninView.as_view(), name='auth-signin'),
    path('signout/', SignoutView.as_view(), name='auth-signout'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('user/', CurrentUserView.as_view(), name='auth-user'),
    path('session/', SessionView.as_view(), name='auth-session'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    
    # Add direct routes for frontend compatibility
    path('users/profiles/me/posts/', UserPostsView.as_view(), name='auth-me-posts'),
    path('users/profiles/me/tasks/', UserTasksView.as_view(), name='auth-me-tasks'),
    
    path('users/', include(router.urls)),
]