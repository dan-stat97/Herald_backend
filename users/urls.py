from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SignupView, SigninView, SignoutView, RefreshView, CurrentUserView,
    UserProfileViewSet, SessionView, ChangePasswordView, UserPostsView, UserTasksView,
    KingsChatAuthView, KingsChatCallbackView,
    PasswordResetRequestView, PasswordResetConfirmView,
)
from .extra_views import UserTaskClaimMeView


router = DefaultRouter()
router.register(r'profiles', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('signup/', SignupView.as_view(), name='auth-signup'),
    path('signin/', SigninView.as_view(), name='auth-signin'),
    path('signout/', SignoutView.as_view(), name='auth-signout'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('kingschat/', KingsChatAuthView.as_view(), name='auth-kingschat'),
    path('kingschat/callback/', KingsChatCallbackView.as_view(), name='auth-kingschat-callback'),
    path('user/', CurrentUserView.as_view(), name='auth-user'),
    path('session/', SessionView.as_view(), name='auth-session'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='auth-password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),

    path('users/profiles/me/', CurrentUserView.as_view(), name='auth-me-profile'),
    path('users/profiles/me/posts/', UserPostsView.as_view(), name='auth-me-posts'),
    path('users/profiles/me/tasks/', UserTasksView.as_view(), name='auth-me-tasks'),
    path('users/profiles/me/tasks/<uuid:task_id>/claim/', UserTaskClaimMeView.as_view(), name='auth-me-task-claim'),

    path('users/', include(router.urls)),
]

