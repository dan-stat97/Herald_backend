# Django Implementation Guide - Herald Social API

## Quick Start

### 1. Project Setup

```bash
# Create Django project
django-admin startproject herald_api .

# Create Django apps
python manage.py startapp users
python manage.py startapp posts
python manage.py startapp wallets
python manage.py startapp communities
python manage.py startapp notifications
```

### 2. Install Required Packages

```bash
pip install django-rest-framework
pip install djangorestframework-simplejwt
pip install django-cors-headers
pip install django-filter
pip install python-decouple
pip install psycopg2-binary  # PostgreSQL adapter
pip install Pillow  # Image processing
pip install celery  # Async tasks
```

### 3. Required Settings

**settings.py**
```python
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # Local apps
    'users.apps.UsersConfig',
    'posts.apps.PostsConfig',
    'wallets.apps.WalletsConfig',
    'communities.apps.CommunitiesConfig',
    'notifications.apps.NotificationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', 5432),
    }
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('SECRET_KEY'),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://heraldsocial.com",
]

AUTH_USER_MODEL = 'auth.User'
```

---

## Django Models

### 1. User Model (users/models.py)

```python
from django.db import models
from django.contrib.auth.models import User
from uuid import uuid4

class UserProfile(models.Model):
    TIER_CHOICES = [
        ('free', 'Free'),
        ('creator', 'Creator'),
        ('premium', 'Premium'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    username = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=200)
    bio = models.TextField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    reputation = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_creator = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['-reputation']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.display_name} (@{self.username})"
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.user.username
        super().save(*args, **kwargs)


class Follow(models.Model):
    follower = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        indexes = [
            models.Index(fields=['follower', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
```

### 2. Post Model (posts/models.py)

```python
from django.db import models
from users.models import UserProfile
from uuid import uuid4

class Post(models.Model):
    MEDIA_TYPE_CHOICES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('reel', 'Reel'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    media = models.FileField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPE_CHOICES, blank=True, null=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)
    httn_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['-likes_count']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Post by {self.author.username} - {self.content[:50]}"


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username}"


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} likes {self.post.id}"


class PostShare(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_shares')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('post', 'user')
```

### 3. Wallet Model (wallets/models.py)

```python
from django.db import models
from users.models import UserProfile
from uuid import uuid4

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='wallet')
    httn_points = models.IntegerField(default=0)
    httn_tokens = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    espees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_rewards = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
    
    def __str__(self):
        return f"Wallet for {self.user.username}"


class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('earn', 'Earn'),
        ('spend', 'Spend'),
        ('convert', 'Convert'),
        ('withdraw', 'Withdraw'),
        ('deposit', 'Deposit'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=20)  # points, tokens, espees
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.currency}"
```

### 4. Community Model (communities/models.py)

```python
from django.db import models
from users.models import UserProfile
from uuid import uuid4

class Community(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='created_communities')
    image_url = models.URLField(blank=True, null=True)
    image = models.ImageField(upload_to='communities/', blank=True, null=True)
    is_private = models.BooleanField(default=False)
    member_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'communities'
        indexes = [
            models.Index(fields=['-member_count']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('community', 'user')
    
    def __str__(self):
        return f"{self.user.username} in {self.community.name}"
```

### 5. Notification Model (notifications/models.py)

```python
from django.db import models
from users.models import UserProfile
from uuid import uuid4

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('share', 'Share'),
        ('mention', 'Mention'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_resource_type = models.CharField(max_length=50)  # post, comment, user
    related_resource_id = models.CharField(max_length=100)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'read']),
        ]
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
```

---

## Django REST Serializers

### 1. User Serializers (users/serializers.py)

```python
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Follow

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'username', 'display_name', 'email', 'bio',
            'avatar_url', 'tier', 'reputation', 'is_verified',
            'is_creator', 'followers_count', 'following_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reputation', 'created_at', 'updated_at']
    
    def get_email(self, obj):
        return obj.user.email
    
    def get_followers_count(self, obj):
        return obj.followers.count()
    
    def get_following_count(self, obj):
        return obj.following.count()


class UserSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    username = serializers.CharField(max_length=100)
    display_name = serializers.CharField(max_length=200)
    full_name = serializers.CharField(max_length=200, required=False)
    
    def validate_username(self, value):
        if UserProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        # Create Django User
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('full_name', '').split()[0] if validated_data.get('full_name') else ''
        )
        
        # Create UserProfile
        profile = UserProfile.objects.create(
            user=user,
            username=validated_data['username'],
            display_name=validated_data['display_name']
        )
        
        return profile


class FollowSerializer(serializers.ModelSerializer):
    follower = UserProfileSerializer()
    following = UserProfileSerializer()
    
    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['id', 'created_at']
```

### 2. Post Serializers (posts/serializers.py)

```python
from rest_framework import serializers
from .models import Post, Comment, PostLike
from users.serializers import UserProfileSerializer

class CommentSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'likes_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'likes_count', 'created_at', 'updated_at']


class PostSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'content', 'media_url', 'media_type',
            'likes_count', 'comments_count', 'shares_count', 'httn_earned',
            'is_liked', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'likes_count', 'comments_count', 'shares_count', 'httn_earned', 'created_at', 'updated_at']
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(post=obj, user=request.user.profile).exists()
        return False


class PostCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['content', 'media_url', 'media_type']
    
    def create(self, validated_data):
        post = Post.objects.create(
            author=self.context['request'].user.profile,
            **validated_data
        )
        return post
```

### 3. Wallet Serializers (wallets/serializers.py)

```python
from rest_framework import serializers
from .models import Wallet, Transaction

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_type', 'amount', 'currency', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'httn_points', 'httn_tokens', 'espees',
            'pending_rewards', 'transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

---

## Django Views (ViewSets)

### 1. User Views (users/views.py)

```python
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import UserProfile, Follow
from .serializers import UserProfileSerializer, UserSignupSerializer, FollowSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_fields = ['username', 'tier', 'is_creator']
    search_fields = ['username', 'display_name']
    ordering_fields = ['-reputation', '-created_at']
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def signup(self, request):
        serializer = UserSignupSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save()
            
            # Create wallet for new user
            from wallets.models import Wallet
            Wallet.objects.create(user=profile)
            
            # Generate tokens
            refresh = RefreshToken.for_user(profile.user)
            return Response({
                'user': UserProfileSerializer(profile).data,
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'token_type': 'Bearer'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def follow(self, request, pk=None):
        try:
            user_to_follow = self.get_object()
            follower_profile = request.user.profile
            
            if user_to_follow == follower_profile:
                return Response({'error': 'Cannot follow yourself'}, status=status.HTTP_400_BAD_REQUEST)
            
            follow, created = Follow.objects.get_or_create(
                follower=follower_profile,
                following=user_to_follow
            )
            
            if created:
                return Response({
                    'success': True,
                    'followers_count': user_to_follow.followers.count()
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Already following'}, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unfollow(self, request, pk=None):
        try:
            user_to_unfollow = self.get_object()
            follower_profile = request.user.profile
            
            Follow.objects.filter(
                follower=follower_profile,
                following=user_to_unfollow
            ).delete()
            
            return Response({
                'success': True,
                'followers_count': user_to_unfollow.followers.count()
            })
        except UserProfile.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def followers(self, request):
        profile = request.user.profile
        followers = profile.followers.all()
        page = self.paginate_queryset(followers)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserProfileSerializer(followers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def following(self, request):
        profile = request.user.profile
        following = profile.following.all()
        page = self.paginate_queryset(following)
        if page is not None:
            serializer = UserProfileSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserProfileSerializer(following, many=True)
        return Response(serializer.data)
```

### 2. Post Views (posts/views.py)

```python
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Post, Comment, PostLike
from .serializers import PostSerializer, PostCreateSerializer, CommentSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_fields = ['media_type']
    search_fields = ['content']
    ordering_fields = ['-created_at', '-likes_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PostCreateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user.profile)
    
    def perform_destroy(self, instance):
        if instance.author.user == self.request.user:
            instance.delete()
        else:
            raise permissions.PermissionDenied("You can only delete your own posts")
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(
            post=post,
            user=request.user.profile
        )
        if created:
            post.likes_count += 1
            post.save()
        return Response({
            'success': True,
            'likes_count': post.likes_count
        })
    
    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unlike(self, request, pk=None):
        post = self.get_object()
        PostLike.objects.filter(post=post, user=request.user.profile).delete()
        post.likes_count = post.post_likes.count()
        post.save()
        return Response({
            'success': True,
            'likes_count': post.likes_count
        })
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        post = self.get_object()
        comments = post.comments.all()
        page = self.paginate_queryset(comments)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_comment(self, request, pk=None):
        post = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(post=post, author=request.user.profile)
            post.comments_count += 1
            post.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 3. Wallet Views (wallets/views.py)

```python
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, Transaction
from .serializers import WalletSerializer, TransactionSerializer

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user.profile)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        wallet = Wallet.objects.get(user=request.user.profile)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def transactions(self, request):
        wallet = Wallet.objects.get(user=request.user.profile)
        transactions = wallet.transactions.all()
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def convert(self, request):
        wallet = Wallet.objects.get(user=request.user.profile)
        from_currency = request.data.get('from_currency')
        to_currency = request.data.get('to_currency')
        amount = request.data.get('amount')
        
        if from_currency == 'points' and to_currency == 'tokens':
            if wallet.httn_points >= amount:
                wallet.httn_points -= amount
                wallet.httn_tokens += amount * 0.1  # 1 point = 0.1 token
                wallet.save()
                
                Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='convert',
                    amount=amount,
                    currency='points',
                    description=f'Converted {amount} points to tokens'
                )
                
                return Response({
                    'success': True,
                    'balance': WalletSerializer(wallet).data
                })
        
        return Response({'error': 'Invalid conversion'}, status=status.HTTP_400_BAD_REQUEST)
```

---

## URL Configuration

### urls.py

```python
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserViewSet
from posts.views import PostViewSet
from wallets.views import WalletViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'wallets', WalletViewSet, basename='wallet')
# Register other ViewSets as needed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('rest_framework.urls')),
]
```

---

## Management Commands

### Create Tasks (management/commands/create_daily_tasks.py)

```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import UserProfile
from tasks.models import UserTask

class Command(BaseCommand):
    help = 'Create daily tasks for all users'
    
    def handle(self, *args, **options):
        users = UserProfile.objects.all()
        for user in users:
            for task_data in DAILY_TASKS:
                UserTask.objects.get_or_create(
                    user=user,
                    title=task_data['title'],
                    defaults={
                        'description': task_data['description'],
                        'task_type': 'daily',
                        'reward': task_data['reward'],
                        'target': task_data['target'],
                    }
                )
        self.stdout.write('Daily tasks created successfully')

DAILY_TASKS = [
    {'title': 'Post Daily', 'description': 'Create a post', 'reward': 50, 'target': 1},
    {'title': 'Like 5 Posts', 'description': 'Like 5 posts', 'reward': 25, 'target': 5},
    {'title': 'Follow 2 Users', 'description': 'Follow 2 new users', 'reward': 30, 'target': 2},
]
```

---

## Celery Tasks (tasks.py)

```python
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Post, UserTask, Wallet

@shared_task
def calculate_post_rewards():
    """Calculate HTTN rewards for top posts daily"""
    yesterday = timezone.now() - timedelta(days=1)
    posts = Post.objects.filter(created_at__date=yesterday).order_by('-likes_count')[:10]
    
    for i, post in enumerate(posts):
        reward = 100 - (i * 10)  # Top post: 100, 2nd: 90, etc.
        post.httn_earned = reward
        post.save()
        
        # Add to user wallet
        wallet = post.author.wallet
        wallet.httn_points += reward
        wallet.save()

@shared_task
def send_notifications():
    """Send pending notifications"""
    from notifications.models import Notification
    pending = Notification.objects.filter(sent=False)
    for notification in pending:
        # Send email or push notification
        notification.sent = True
        notification.save()
```

---

## Environment Variables (.env)

```
# Database
DB_NAME=herald_db
DB_USER=postgres
DB_PASSWORD=securepassword
DB_HOST=localhost
DB_PORT=5432

# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# JWT
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for media uploads)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_STORAGE_BUCKET_NAME=herald-social-media

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## Migration Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load fixtures
python manage.py loaddata fixtures/initial_data.json
```

---

## Testing

### tests.py Template

```python
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from users.models import UserProfile

class UserAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            username='testuser',
            display_name='Test User'
        )
    
    def test_get_user_profile(self):
        response = self.client.get(f'/api/v1/users/{self.profile.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_update_user_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch('/api/v1/users/me/', {
            'display_name': 'Updated Name'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['display_name'], 'Updated Name')
```

---

## Deployment Checklist

- [ ] Database setup and migrations
- [ ] Environment variables configured
- [ ] Static files collected (`collectstatic`)
- [ ] Media storage configured (AWS S3)
- [ ] Email backend configured
- [ ] Redis cache running
- [ ] Celery workers running
- [ ] CORS properly configured
- [ ] SSL certificates installed
- [ ] Admin panel accessible
- [ ] Health checks working
- [ ] Logging configured
- [ ] Monitoring set up

---

**Status**: Ready for Implementation  
**Created**: February 26, 2026
