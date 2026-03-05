from rest_framework import serializers
from .models import Cause


class CauseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    progress_percent = serializers.SerializerMethodField()
    
    class Meta:
        model = Cause
        fields = [
            'id', 'title', 'description', 'category', 'created_by', 'created_by_username',
            'goal_amount', 'raised_amount', 'progress_percent', 'image_url', 'status',
            'created_at', 'end_date'
        ]
        read_only_fields = ['id', 'created_by', 'raised_amount', 'created_at']
    
    def get_progress_percent(self, obj):
        if obj.goal_amount > 0:
            return round((obj.raised_amount / obj.goal_amount) * 100, 2)
        return 0
