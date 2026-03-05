from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination
from wallets.models import Wallet, Transaction
from users.models import User as UserProfile
from django.db import transaction as db_transaction
from decimal import Decimal


class WalletTransactionsView(APIView):
    """Get user's transaction history"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
            
            # Get transactions
            transactions = Transaction.objects.filter(wallet_id=wallet).order_by('-created_at')
            
            # Paginate
            paginator = PageNumberPagination()
            paginator.page_size = int(request.query_params.get('limit', 50))
            page = paginator.paginate_queryset(transactions, request)
            
            transactions_data = [{
                'id': txn.id,
                'transaction_type': txn.transaction_type,
                'amount': txn.amount,
                'currency': txn.currency,
                'description': txn.description,
                'created_at': txn.created_at
            } for txn in page]
            
            return paginator.get_paginated_response(transactions_data)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch transactions: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletConvertView(APIView):
    """Convert between currencies (Points to Tokens)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
            
            from_currency = request.data.get('from_currency')
            to_currency = request.data.get('to_currency')
            amount = request.data.get('amount')
            
            if not all([from_currency, to_currency, amount]):
                return Response(
                    {'error': 'from_currency, to_currency, and amount are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            amount = Decimal(str(amount))
            
            # Conversion rates (you can adjust these)
            conversion_rates = {
                'points_to_tokens': Decimal('0.01'),  # 100 points = 1 token
                'tokens_to_espees': Decimal('1.0'),   # 1 token = 1 espee
            }
            
            with db_transaction.atomic():
                if from_currency == 'points' and to_currency == 'tokens':
                    if wallet.httn_points < amount:
                        return Response(
                            {'error': f'Insufficient points. Available: {wallet.httn_points}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    converted_amount = amount * conversion_rates['points_to_tokens']
                    wallet.httn_points -= int(amount)
                    wallet.httn_tokens += converted_amount
                    
                elif from_currency == 'tokens' and to_currency == 'espees':
                    if wallet.httn_tokens < amount:
                        return Response(
                            {'error': f'Insufficient tokens. Available: {wallet.httn_tokens}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    converted_amount = amount * conversion_rates['tokens_to_espees']
                    wallet.httn_tokens -= amount
                    wallet.espees += converted_amount
                    
                else:
                    return Response(
                        {'error': 'Invalid conversion pair. Supported: points->tokens, tokens->espees'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                wallet.save()
                
                # Create transaction record
                Transaction.objects.create(
                    wallet_id=wallet,
                    transaction_type='conversion',
                    amount=amount,
                    currency=from_currency,
                    description=f'Converted {amount} {from_currency} to {converted_amount} {to_currency}'
                )
            
            return Response({
                'success': True,
                'message': f'Converted {amount} {from_currency} to {converted_amount} {to_currency}',
                'new_balance': {
                    'httn_points': wallet.httn_points,
                    'httn_tokens': wallet.httn_tokens,
                    'espees': wallet.espees
                }
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to convert: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletWithdrawView(APIView):
    """Withdraw funds from wallet"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            wallet = Wallet.objects.get(user_id=profile)
            
            amount = request.data.get('amount')
            payment_method = request.data.get('payment_method')
            
            if not all([amount, payment_method]):
                return Response(
                    {'error': 'amount and payment_method are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            amount = Decimal(str(amount))
            
            if payment_method not in ['bank', 'crypto']:
                return Response(
                    {'error': 'Invalid payment method. Use: bank or crypto'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check balance
            if wallet.espees < amount:
                return Response(
                    {'error': f'Insufficient balance. Available: {wallet.espees}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Minimum withdrawal amount
            if amount < Decimal('10.00'):
                return Response(
                    {'error': 'Minimum withdrawal amount is 10.00 Espees'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with db_transaction.atomic():
                # Deduct from balance
                wallet.espees -= amount
                wallet.save()
                
                # Create withdrawal transaction
                txn = Transaction.objects.create(
                    wallet_id=wallet,
                    transaction_type='withdrawal',
                    amount=amount,
                    currency='espees',
                    description=f'Withdrawal to {payment_method}'
                )
            
            return Response({
                'success': True,
                'message': f'Withdrawal of {amount} Espees initiated',
                'transaction_id': str(txn.id),
                'payment_method': payment_method,
                'new_balance': wallet.espees
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Wallet.DoesNotExist:
            return Response(
                {'error': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to process withdrawal: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
