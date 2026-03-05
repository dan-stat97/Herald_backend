from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Task, UserTask


class TaskViewSet(viewsets.ModelViewSet):
    """CRUD operations for tasks"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
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
        try:
            user_task = self.get_object()
            
            if not user_task.completed:
                return Response(
                    {'error': 'Task not completed yet'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if user_task.claimed:
                return Response(
                    {'error': 'Reward already claimed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Award reward
            from wallets.models import Wallet
            from users.models import User as UserProfile
            
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
            
            wallet.httn_points += user_task.task.reward
            wallet.save()
            
            user_task.claimed = True
            user_task.save()
            
            return Response({
                'success': True,
                'message': f'Claimed {user_task.task.reward} HTTN Points',
                'reward': user_task.task.reward,
                'new_balance': wallet.httn_points
            }, status=status.HTTP_200_OK)
            
        except UserTask.DoesNotExist:
            return Response({'error': 'Task not found'}, status=404)
        except Exception as e:
            return Response(
                {'error': f'Failed to claim reward: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
