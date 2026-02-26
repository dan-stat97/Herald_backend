# core/serializers.py
from rest_framework import serializers
from .models import (
    Profiles, Posts, Likes, Reposts, Hashtags, 
    Transactions, News, Communities, Causes, Notifications,
    Comment, Follow, Bookmark,  # Add these
    AdCampaigns, PostInteractions, UserRoles, UserSettings, UserTasks, Wallets
)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profiles
        fields = '__all__'
class PostSerializer(serializers.ModelSerializer):
    user_details = ProfileSerializer(source='user', read_only=True)
    comments_count = serializers.IntegerField(source='replies_count', read_only=True)
    
    class Meta:
        model = Posts
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'likes_count', 'replies_count', 'reposts_count']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Likes
        fields = '__all__'

class RepostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reposts
        fields = '__all__'

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtags
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = '__all__'

class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = '__all__'

class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Communities
        fields = '__all__'

class CauseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Causes
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = '__all__'

# ===== NEW SERIALIZERS =====

class CommentSerializer(serializers.ModelSerializer):
    author = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['id', 'likes_count', 'created_at', 'updated_at']

class FollowSerializer(serializers.ModelSerializer):
    follower = ProfileSerializer(read_only=True)
    following = ProfileSerializer(read_only=True)
    
    class Meta:
        model = Follow
        fields = '__all__'

class BookmarkSerializer(serializers.ModelSerializer):
    post = PostSerializer(read_only=True)
    
    class Meta:
        model = Bookmark
        fields = '__all__'