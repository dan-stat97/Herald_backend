from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    # Expose 'type' as an alias for notification_type for frontend compatibility
    type = serializers.CharField(source='notification_type', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'user_id', 'notification_type', 'type',
            'title', 'message',
            'related_resource_type', 'related_resource_id',
            'actor_id', 'actor_name', 'actor_avatar', 'actor_verified',
            'read', 'created_at',
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'type']
