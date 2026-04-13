from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from datetime import timedelta
import uuid
from django.utils import timezone
from .models import LiveStream, StreamChatMessage, StreamDonation, StreamViewerEvent
from .ivs_service import (
    IVSProvisioningError,
    create_host_session,
    ivs_is_enabled,
    provision_stream_resource,
)
from .ranking import rank_streams_for_discovery
from core.pagination import StandardPagination


class LiveStreamSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source='user.id', read_only=True)
    host = serializers.SerializerMethodField()

    class Meta:
        model = LiveStream
        fields = [
            'id', 'user_id', 'host', 'title', 'description',
            'provider', 'status', 'stream_url', 'playback_url', 'thumbnail_url',
            'ingest_endpoint', 'provider_stream_key', 'ivs_channel_arn', 'ivs_stage_arn',
            'ivs_stage_rtmps_endpoint', 'ivs_stage_whip_endpoint', 'host_token_expires_at',
            'viewer_count',
            'started_at', 'ended_at', 'scheduled_for', 'created_at'
        ]
        read_only_fields = [
            'id', 'user_id', 'host', 'playback_url', 'ingest_endpoint',
            'provider_stream_key', 'ivs_channel_arn', 'ivs_stage_arn',
            'ivs_stage_rtmps_endpoint', 'ivs_stage_whip_endpoint',
            'host_token_expires_at', 'viewer_count', 'started_at', 'ended_at', 'created_at'
        ]

    def validate(self, attrs):
        provider = attrs.get('provider') or getattr(self.instance, 'provider', None)
        if not provider:
            provider = 'ivs' if ivs_is_enabled() else 'manual'
            attrs['provider'] = provider

        status_value = attrs.get('status') or getattr(self.instance, 'status', 'scheduled')
        scheduled_for = attrs.get('scheduled_for')
        stream_url = attrs.get('stream_url')

        if status_value == 'scheduled' and not scheduled_for and not self.instance:
            attrs['scheduled_for'] = timezone.now() + timedelta(hours=1)

        if provider == 'manual' and status_value == 'live' and not stream_url:
            raise serializers.ValidationError({'stream_url': 'A stream URL is required to go live.'})

        return attrs

    def get_host(self, obj):
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username,
            'display_name': user.display_name or user.username,
            'avatar_url': user.avatar_url,
            'is_verified': bool(user.is_verified),
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        is_owner = bool(
            request and
            request.user and
            request.user.is_authenticated and
            str(instance.user.user_id) == str(request.user.id)
        )

        if not is_owner:
            for field in (
                'ingest_endpoint',
                'provider_stream_key',
                'ivs_channel_arn',
                'ivs_stage_arn',
                'ivs_stage_rtmps_endpoint',
                'ivs_stage_whip_endpoint',
                'host_token_expires_at',
            ):
                data.pop(field, None)

        return data


class StreamChatMessageSerializer(serializers.ModelSerializer):
    stream_id = serializers.UUIDField(source='stream.id', read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = StreamChatMessage
        fields = ['id', 'stream_id', 'user', 'message', 'created_at']
        read_only_fields = ['id', 'stream_id', 'user', 'created_at']

    def get_user(self, obj):
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username,
            'display_name': user.display_name or user.username,
            'avatar_url': user.avatar_url,
        }


class StreamDonationSerializer(serializers.ModelSerializer):
    stream_id = serializers.UUIDField(source='stream.id', read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = StreamDonation
        fields = ['id', 'stream_id', 'user', 'amount', 'currency', 'message', 'created_at']
        read_only_fields = ['id', 'stream_id', 'user', 'created_at']

    def get_user(self, obj):
        user = obj.user
        return {
            'id': str(user.id),
            'username': user.username,
            'display_name': user.display_name or user.username,
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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        status_filter = request.query_params.get('status')

        if status_filter in ('live', 'scheduled'):
            candidate_limit = min(max(int(request.query_params.get('limit', 20)), 20) * 8, 200)
            ranked_items = rank_streams_for_discovery(queryset, request, candidate_limit=candidate_limit)
        else:
            ranked_items = queryset

        page = self.paginate_queryset(ranked_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ranked_items, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        """Create stream with authenticated user"""
        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            status_value = serializer.validated_data.get('status', 'scheduled')
            provider = serializer.validated_data.get('provider', 'manual')
            extra_fields = {}
            if status_value == 'live':
                extra_fields['started_at'] = timezone.now()

            if provider == 'ivs':
                stream_id = str(uuid.uuid4())
                provisioned = provision_stream_resource(
                    stream_id=stream_id,
                    title=serializer.validated_data.get('title', 'Herald Live'),
                    record_enabled=False,
                )
                extra_fields.update({
                    'id': stream_id,
                    'provider': provisioned.provider,
                    'playback_url': provisioned.playback_url,
                    'stream_url': provisioned.playback_url,
                    'ingest_endpoint': provisioned.ingest_endpoint,
                    'provider_stream_key': provisioned.provider_stream_key,
                    'ivs_channel_arn': provisioned.ivs_channel_arn,
                    'ivs_stage_arn': provisioned.ivs_stage_arn,
                    'ivs_stage_rtmps_endpoint': provisioned.ivs_stage_rtmps_endpoint,
                    'ivs_stage_whip_endpoint': provisioned.ivs_stage_whip_endpoint,
                })
            serializer.save(user=profile, **extra_fields)
        except IVSProvisioningError as exc:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'provider': str(exc)})
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

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def host_session(self, request, pk=None):
        stream = self.get_object()

        if str(stream.user.user_id) != str(request.user.id):
            return Response({'detail': 'Only the stream owner can open a host session.'}, status=status.HTTP_403_FORBIDDEN)

        if stream.provider != 'ivs' or not stream.ivs_stage_arn:
            return Response({
                'provider': stream.provider,
                'playback_url': stream.playback_url or stream.stream_url,
                'ingest_endpoint': stream.ingest_endpoint,
                'provider_stream_key': stream.provider_stream_key,
                'detail': 'This stream is not using Amazon IVS yet.',
            })

        try:
            display_name = request.user.get_full_name() or request.user.username
            session = create_host_session(
                stage_arn=stream.ivs_stage_arn,
                user_id=str(request.user.id),
                display_name=display_name,
            )
            stream.host_token_expires_at = session.expires_at
            stream.save(update_fields=['host_token_expires_at'])
            return Response({
                'provider': stream.provider,
                'stage_arn': session.stage_arn,
                'participant_token': session.token,
                'participant_id': session.participant_id,
                'token_expires_at': session.expires_at,
                'rtmps_endpoint': session.rtmps_endpoint or stream.ivs_stage_rtmps_endpoint,
                'whip_endpoint': session.whip_endpoint or stream.ivs_stage_whip_endpoint,
                'playback_url': stream.playback_url or stream.stream_url,
                'ingest_endpoint': stream.ingest_endpoint,
            })
        except IVSProvisioningError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def chat(self, request, pk=None):
        stream = self.get_object()

        if request.method == 'GET':
            limit = int(request.query_params.get('limit', 40))
            messages = stream.chat_messages.select_related('user').all()[:limit]
            serializer = StreamChatMessageSerializer(messages, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        message = (request.data.get('message') or '').strip()
        if not message:
            return Response({'message': ['Message is required.']}, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        created = StreamChatMessage.objects.create(
            stream=stream,
            user=profile,
            message=message,
        )
        serializer = StreamChatMessageSerializer(created)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def donations(self, request, pk=None):
        stream = self.get_object()

        if request.method == 'GET':
            limit = int(request.query_params.get('limit', 20))
            donations = stream.donations.select_related('user').all()[:limit]
            serializer = StreamDonationSerializer(donations, many=True)
            return Response(serializer.data)

        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        amount = request.data.get('amount')
        currency = request.data.get('currency') or 'espees'
        message = (request.data.get('message') or '').strip() or None

        try:
            amount_value = float(amount)
        except (TypeError, ValueError):
            return Response({'amount': ['Enter a valid amount.']}, status=status.HTTP_400_BAD_REQUEST)

        if amount_value <= 0:
            return Response({'amount': ['Amount must be greater than zero.']}, status=status.HTTP_400_BAD_REQUEST)

        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        created = StreamDonation.objects.create(
            stream=stream,
            user=profile,
            amount=amount_value,
            currency=currency,
            message=message,
        )
        serializer = StreamDonationSerializer(created)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='viewer-join')
    def viewer_join(self, request, pk=None):
        return self._record_viewer_event(request, pk, 'join')

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated], url_path='viewer-leave')
    def viewer_leave(self, request, pk=None):
        return self._record_viewer_event(request, pk, 'leave')

    def _record_viewer_event(self, request, pk, event_type):
        stream = self.get_object()

        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=request.user)
        except UserProfile.DoesNotExist:
            return Response({'detail': 'User profile not found.'}, status=status.HTTP_400_BAD_REQUEST)

        StreamViewerEvent.objects.create(
            stream=stream,
            user=profile,
            event_type=event_type,
        )

        if event_type == 'join':
            stream.viewer_count = (stream.viewer_count or 0) + 1
        else:
            stream.viewer_count = max((stream.viewer_count or 0) - 1, 0)
        stream.save(update_fields=['viewer_count'])

        return Response({
            'success': True,
            'event_type': event_type,
            'viewer_count': stream.viewer_count,
        })
