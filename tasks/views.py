from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Task, UserTask
from .rewards import claim_user_task_reward, ensure_default_tasks


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD operations for tasks"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            ensure_default_tasks(profile)
            return UserTask.objects.filter(user=profile).select_related('task')
        except UserProfile.DoesNotExist:
            return UserTask.objects.none()
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class UserTaskSerializer(serializers.ModelSerializer):
            title = serializers.CharField(source='task.title', read_only=True)
            description = serializers.CharField(source='task.description', read_only=True)
            task_type = serializers.CharField(source='task.task_type', read_only=True)
            reward = serializers.IntegerField(source='task.reward', read_only=True)
            target = serializers.IntegerField(source='task.target', read_only=True)
            progress_percent = serializers.SerializerMethodField()
            
            class Meta:
                model = UserTask
                fields = [
                    'id', 'title', 'description', 'task_type', 'reward', 'target',
                    'progress', 'progress_percent', 'completed', 'claimed', 'completed_at', 'created_at'
                ]
            
            def get_progress_percent(self, obj):
                if obj.task.target > 0:
                    return min(round((obj.progress / obj.task.target) * 100, 2), 100)
                return 0
        
        return UserTaskSerializer
    
    @action(detail=True, methods=['post'])
    def claim(self, request, pk=None):
        """Claim task reward"""
        from users.models import User as UserProfile

        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)

        _, payload, status_code = claim_user_task_reward(profile, pk)
        return Response(payload, status=status_code)
