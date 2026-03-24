from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from .models import LiveStream
from core.pagination import StandardPagination


class LiveStreamSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    host = serializers.SerializerMethodField()

    class Meta:
        model = LiveStream
        fields = [
            'id', 'user_id', 'host', 'title', 'description',
            'status', 'stream_url', 'thumbnail_url', 'viewer_count',
            'started_at', 'ended_at', 'scheduled_for', 'created_at'
        ]
        read_only_fields = ['id', 'user_id', 'host', 'viewer_count', 'started_at', 'ended_at', 'created_at']

    def get_host(self, obj):
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username,
            'display_name': user.display_name or user.username,
            'avatar_url': user.avatar_url,
            'is_verified': bool(user.is_verified),
        }


class LiveStreamViewSet(viewsets.ModelViewSet):
    """CRUD operations for live streams"""
    serializer_class = LiveStreamSerializer
    pagination_class = StandardPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        status_filter = self.request.query_params.get('status')
        queryset = LiveStream.objects.all().select_related('user')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if status_filter == 'live':
            queryset = queryset.order_by('-viewer_count', '-started_at', '-created_at')
        elif status_filter == 'scheduled':
            queryset = queryset.order_by('scheduled_for', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset
    
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
