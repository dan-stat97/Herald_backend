
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer
from users.models import User as UserProfile

class NotificationViewSet(viewsets.ModelViewSet):
	serializer_class = NotificationSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = UserProfile.objects.get(user_id=self.request.user)
		queryset = Notification.objects.filter(user_id=user).order_by('-created_at')
		read = self.request.query_params.get('read')
		if read is not None:
			queryset = queryset.filter(read=(read.lower() == 'true'))
		return queryset

	@action(detail=True, methods=['patch'])
	def mark_read(self, request, pk=None):
		notification = self.get_object()
		notification.read = True
		notification.save()
		return Response(self.get_serializer(notification).data)

	@action(detail=True, methods=['post'], url_path='mark_as_read')
	def mark_as_read(self, request, pk=None):
		notification = self.get_object()
		notification.read = True
		notification.save()
		return Response(self.get_serializer(notification).data)

	@action(detail=False, methods=['post'])
	def mark_all_read(self, request):
		user = UserProfile.objects.get(user_id=request.user)
		Notification.objects.filter(user_id=user, read=False).update(read=True)
		return Response({'success': True})
