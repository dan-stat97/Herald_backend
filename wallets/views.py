
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet
from .serializers import WalletSerializer
from users.models import User as UserProfile

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Wallet.objects.all()
	serializer_class = WalletSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=False, methods=['get'], url_path='me')
	def me(self, request):
		profile = UserProfile.objects.get(user_id=request.user)
		wallet = Wallet.objects.get(user_id=profile)
		return Response(WalletSerializer(wallet).data)
