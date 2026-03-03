
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet
from .serializers import WalletSerializer
from users.models import User as UserProfile
import uuid

class WalletViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = Wallet.objects.all()
	serializer_class = WalletSerializer
	permission_classes = [permissions.IsAuthenticated]

	@action(detail=False, methods=['get'], url_path='me')
	def me(self, request):
		try:
			profile = UserProfile.objects.get(user_id=request.user)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)
		except Exception as e:
			print(f"Error getting user profile: {e}")
			return Response({'error': 'Failed to retrieve user profile'}, status=500)
		
		try:
			wallet, created = Wallet.objects.get_or_create(user_id=profile)
			if created:
				print(f"Created new wallet for user {profile.username}")
			return Response(WalletSerializer(wallet).data)
		except Exception as e:
			print(f"Error creating/getting wallet: {e}")
			return Response({'error': 'Failed to retrieve wallet'}, status=500)

	@action(detail=False, methods=['get'], url_path='me/balance')
	def balance(self, request):
		try:
			profile = UserProfile.objects.get(user_id=request.user)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)
		
		wallet, created = Wallet.objects.get_or_create(user_id=profile)
		return Response({
			'httn_points': wallet.httn_points,
			'httn_tokens': str(wallet.httn_tokens),
			'espees': str(wallet.espees),
			'pending_rewards': wallet.pending_rewards,
		})

	@action(detail=False, methods=['get'], url_path='me/transactions')
	def transactions(self, request):
		return Response([])

	@action(detail=False, methods=['post'], url_path='me/convert')
	def convert(self, request):
		try:
			profile = UserProfile.objects.get(user_id=request.user)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)
		
		wallet, created = Wallet.objects.get_or_create(user_id=profile)
		from_currency = request.data.get('from_currency')
		to_currency = request.data.get('to_currency')
		amount = int(request.data.get('amount', 0))
		if from_currency == 'points' and to_currency == 'tokens' and amount > 0 and wallet.httn_points >= amount:
			wallet.httn_points -= amount
			wallet.httn_tokens += amount / 10
			wallet.save(update_fields=['httn_points', 'httn_tokens', 'updated_at'])
			return Response({'success': True, 'new_balance': WalletSerializer(wallet).data})
		return Response({'success': False, 'error': 'Invalid conversion request'}, status=400)

	@action(detail=False, methods=['post'], url_path='me/withdraw')
	def withdraw(self, request):
		amount = request.data.get('amount')
		if amount is None:
			return Response({'success': False, 'error': 'amount is required'}, status=400)
		return Response({'success': True, 'transaction_id': str(uuid.uuid4())})
