from rest_framework import views, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Wallet
from users.models import User as UserProfile
from django.db import transaction as db_transaction


class WalletTransferView(views.APIView):
    """Transfer wallet balance between users"""
    permission_classes = [permissions.IsAuthenticated]
    
    @db_transaction.atomic
    def post(self, request):
        """Transfer points/tokens to another user"""
        try:
            # Get sender (current user)
            sender_profile = UserProfile.objects.get(user_id=request.user)
            sender_wallet = Wallet.objects.get(user_id=sender_profile)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Sender profile not found'}, status=404)
        except Wallet.DoesNotExist:
            return Response({'error': 'Sender wallet not found'}, status=404)
        
        # Get recipient
        recipient_id = request.data.get('recipient_id')
        amount = request.data.get('amount')
        currency = request.data.get('currency', 'httn_points')  # httn_points, httn_tokens, espees
        
        if not recipient_id or not amount:
            return Response(
                {'error': 'recipient_id and amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = int(amount) if currency == 'httn_points' else float(amount)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recipient_profile = UserProfile.objects.get(id=recipient_id)
            recipient_wallet = Wallet.objects.get(user_id=recipient_profile)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=404)
        except Wallet.DoesNotExist:
            return Response({'error': 'Recipient wallet not found'}, status=404)
        
        # Validate sender has sufficient balance
        if currency == 'httn_points':
            if sender_wallet.httn_points < amount:
                return Response(
                    {'error': f'Insufficient HTTN Points. Available: {sender_wallet.httn_points}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            sender_wallet.httn_points -= amount
            recipient_wallet.httn_points += amount
            
        elif currency == 'httn_tokens':
            if sender_wallet.httn_tokens < amount:
                return Response(
                    {'error': f'Insufficient HTTN Tokens. Available: {sender_wallet.httn_tokens}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            sender_wallet.httn_tokens -= amount
            recipient_wallet.httn_tokens += amount
            
        elif currency == 'espees':
            if sender_wallet.espees < amount:
                return Response(
                    {'error': f'Insufficient Espees. Available: {sender_wallet.espees}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            sender_wallet.espees -= amount
            recipient_wallet.espees += amount
        else:
            return Response(
                {'error': 'Invalid currency. Use: httn_points, httn_tokens, or espees'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Save both wallets
        sender_wallet.save()
        recipient_wallet.save()
        
        return Response({
            'success': True,
            'message': f'Transferred {amount} {currency} to {recipient_profile.username}',
            'sender_wallet': {
                'httn_points': sender_wallet.httn_points,
                'httn_tokens': str(sender_wallet.httn_tokens),
                'espees': str(sender_wallet.espees),
            },
            'recipient_id': str(recipient_profile.id),
            'recipient_username': recipient_profile.username,
        }, status=status.HTTP_200_OK)
