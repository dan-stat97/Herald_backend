from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import Cause
from .serializers import CauseSerializer
from users.models import User as UserProfile
from wallets.models import Wallet
from django.db import transaction as db_transaction


class CauseViewSet(viewsets.ModelViewSet):
    """CRUD operations for causes/fundraisers"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CauseSerializer
    
    def get_queryset(self):
        return Cause.objects.all().order_by('-raised_amount')
    
    def perform_create(self, serializer):
        """Create cause with authenticated user as creator"""
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            serializer.save(created_by=profile)
        except UserProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("User profile not found")
    
    @action(detail=True, methods=['post'])
    def donate(self, request, pk=None):
        """Donate to a cause"""
        cause = self.get_object()
        amount = request.data.get('amount')
        payment_type = request.data.get('payment_type', 'wallet')
        
        if not amount:
            return Response(
                {'error': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
        except UserProfile.DoesNotExist:
            return Response({'error': 'User profile not found'}, status=404)
        except Wallet.DoesNotExist:
            return Response({'error': 'Wallet not found'}, status=404)
        
        # Check wallet balance
        if payment_type == 'wallet':
            if wallet.espees < amount:
                return Response(
                    {'error': f'Insufficient balance. Available: {wallet.espees}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                # Deduct from wallet
                wallet.espees -= amount
                wallet.save()
                
                # Add to cause
                cause.raised_amount += amount
                cause.save()
                
                return Response({
                    'success': True,
                    'message': f'Donated {amount} to {cause.title}',
                    'cause': {
                        'id': str(cause.id),
                        'title': cause.title,
                        'raised_amount': str(cause.raised_amount),
                        'goal_amount': str(cause.goal_amount),
                        'progress_percent': round((cause.raised_amount / cause.goal_amount) * 100, 2) if cause.goal_amount > 0 else 0
                    }
                }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Only wallet payment is supported currently'},
            status=status.HTTP_400_BAD_REQUEST
        )
