from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import LiveStream


class LiveStreamViewSet(viewsets.ModelViewSet):
    """CRUD operations for live streams"""

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        queryset = LiveStream.objects.all()
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if status_filter == 'live':
            queryset = queryset.order_by('-viewer_count')
        
        return queryset
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class LiveStreamSerializer(serializers.ModelSerializer):
            username = serializers.CharField(source='user.username', read_only=True)
            user_avatar = serializers.URLField(source='user.avatar_url', read_only=True)
            
            class Meta:
                model = LiveStream
                fields = [
                    'id', 'user', 'username', 'user_avatar', 'title', 'description',
                    'status', 'stream_url', 'thumbnail_url', 'viewer_count',
                    'started_at', 'ended_at', 'scheduled_for', 'created_at'
                ]
                read_only_fields = ['id', 'user', 'viewer_count', 'started_at', 'ended_at', 'created_at']
        
        return LiveStreamSerializer
    
    def perform_create(self, serializer):
        """Create stream with authenticated user"""
        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            serializer.save(user=profile)
        except UserProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("User profile not found")
    
    @action(detail=True, methods=['patch'])
    def update_stats(self, request, pk=None):
        """Update stream viewer count and status"""
        stream = self.get_object()
        
        viewer_count = request.data.get('viewer_count')
        stream_status = request.data.get('status')
        
        if viewer_count is not None:
            stream.viewer_count = viewer_count
        
        if stream_status:
            stream.status = stream_status
            
            if stream_status == 'live' and not stream.started_at:
                from django.utils import timezone
                stream.started_at = timezone.now()
            elif stream_status == 'ended' and not stream.ended_at:
                from django.utils import timezone
                stream.ended_at = timezone.now()
        
        stream.save()
        
        serializer = self.get_serializer(stream)
        return Response(serializer.data)
