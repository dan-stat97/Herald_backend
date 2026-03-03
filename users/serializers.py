from rest_framework import serializers
from django.contrib.auth.models import User
from .models import User as UserProfile

class UserSignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(max_length=100)
    full_name = serializers.CharField(max_length=200)
    display_name = serializers.CharField(max_length=200)

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField()
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user_id', 'username', 'display_name', 'full_name', 'email', 'avatar_url', 'bio', 'tier',
            'reputation', 'is_verified', 'is_creator', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user_id', 'reputation', 'created_at', 'updated_at']

    def get_email(self, obj):
        return obj.user_id.email
