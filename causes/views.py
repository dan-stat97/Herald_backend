from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction as db_transaction
from django.db.models import Q
from .models import Cause, Donation
from .serializers import CauseSerializer, DonationSerializer
from users.models import User as UserProfile
from wallets.models import Wallet


def _get_profile(auth_user):
	return UserProfile.objects.get(user_id=auth_user)


class CauseViewSet(viewsets.ModelViewSet):
	serializer_class = CauseSerializer

	def get_permissions(self):
		if self.action in ('list', 'retrieve', 'donors'):
			return [permissions.AllowAny()]
		return [permissions.IsAuthenticated()]

	def get_queryset(self):
		qs = Cause.objects.all()
		category = self.request.query_params.get('category')
		search = self.request.query_params.get('search') or self.request.query_params.get('q')
		status_filter = self.request.query_params.get('status', 'active')
		sort = self.request.query_params.get('sort', '-created_at')

		if category:
			qs = qs.filter(category__icontains=category)

		if search:
			qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

		if status_filter and status_filter != 'all':
			qs = qs.filter(status=status_filter)

		valid_sorts = ('created_at', '-created_at', 'raised_amount', '-raised_amount',
					   'goal_amount', '-goal_amount', 'end_date')
		if sort in valid_sorts:
			qs = qs.order_by(sort)

		return qs

	def get_serializer_context(self):
		ctx = super().get_serializer_context()
		ctx['request'] = self.request
		return ctx

	def perform_create(self, serializer):
		try:
			profile = _get_profile(self.request.user)
			serializer.save(created_by=profile, status='active')
		except UserProfile.DoesNotExist:
			from rest_framework.exceptions import ValidationError
			raise ValidationError("User profile not found")

	@action(detail=True, methods=['post'])
	def donate(self, request, pk=None):
		cause = self.get_object()

		if cause.status != 'active':
			return Response({'error': 'This cause is no longer accepting donations'},
							status=status.HTTP_400_BAD_REQUEST)

		amount_raw = request.data.get('amount')
		if not amount_raw:
			return Response({'error': 'amount is required'}, status=status.HTTP_400_BAD_REQUEST)

		try:
			amount = float(amount_raw)
			if amount <= 0:
				raise ValueError()
		except (ValueError, TypeError):
			return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

		message = request.data.get('message', '').strip()
		is_anonymous = bool(request.data.get('is_anonymous', False))

		try:
			profile = _get_profile(request.user)
			wallet = Wallet.objects.get(user_id=profile)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)
		except Wallet.DoesNotExist:
			return Response({'error': 'Wallet not found'}, status=404)

		if float(wallet.espees) < amount:
			return Response(
				{'error': f'Insufficient Espees balance. Available: {wallet.espees}'},
				status=status.HTTP_400_BAD_REQUEST
			)

		with db_transaction.atomic():
			wallet.espees -= amount
			wallet.save(update_fields=['espees'])

			cause.raised_amount += amount
			if float(cause.raised_amount) >= float(cause.goal_amount):
				cause.status = 'completed'
			cause.save(update_fields=['raised_amount', 'status'])

			Donation.objects.create(
				cause=cause,
				donor=profile,
				amount=amount,
				message=message or None,
				is_anonymous=is_anonymous,
			)

		return Response({
			'success': True,
			'message': f'Donated {amount:,.2f} Espees to "{cause.title}"',
			'cause': CauseSerializer(cause, context={'request': request}).data,
			'wallet_balance': float(wallet.espees),
		})

	@action(detail=True, methods=['get'])
	def donors(self, request, pk=None):
		cause = self.get_object()
		donations = cause.donations.select_related('donor').filter(is_anonymous=False)[:50]
		return Response(DonationSerializer(donations, many=True).data)

	@action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
	def my_donations(self, request):
		try:
			profile = _get_profile(request.user)
		except UserProfile.DoesNotExist:
			return Response({'error': 'User profile not found'}, status=404)
		donations = Donation.objects.filter(donor=profile).select_related('cause')[:50]
		data = [
			{
				'id': str(d.id),
				'amount': float(d.amount),
				'message': d.message,
				'created_at': d.created_at.isoformat(),
				'cause': CauseSerializer(d.cause, context={'request': request}).data,
			}
			for d in donations
		]
		return Response(data)
