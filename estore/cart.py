from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Cart, Product
from users.models import User as UserProfile
from decimal import Decimal


class CartView(APIView):
    """Get user's cart"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            cart, created = Cart.objects.get_or_create(user=profile)
            
            return Response({
                'id': cart.id,
                'items': cart.items,
                'total_amount': cart.total_amount,
                'created_at': cart.created_at
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch cart: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CartItemView(APIView):
    """Add/remove items from cart"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Add item to cart"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            cart, created = Cart.objects.get_or_create(user=profile)
            
            product_id = request.data.get('product_id')
            quantity = request.data.get('quantity', 1)
            
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify product exists
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Add item to cart
            items = cart.items if cart.items else []
            
            # Check if item already in cart
            item_found = False
            for item in items:
                if item.get('product_id') == str(product_id):
                    item['quantity'] = item.get('quantity', 0) + quantity
                    item_found = True
                    break
            
            if not item_found:
                items.append({
                    'product_id': str(product_id),
                    'product_name': product.name,
                    'price': str(product.price),
                    'quantity': quantity
                })
            
            # Recalculate total
            total = Decimal('0.00')
            for item in items:
                total += Decimal(item['price']) * item['quantity']
            
            cart.items = items
            cart.total_amount = total
            cart.save()
            
            return Response({
                'success': True,
                'cart': {
                    'id': cart.id,
                    'items': cart.items,
                    'total_amount': cart.total_amount
                }
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to add item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, product_id):
        """Remove item from cart"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            cart = Cart.objects.get(user=profile)
            
            # Remove item from cart
            items = cart.items if cart.items else []
            items = [item for item in items if item.get('product_id') != str(product_id)]
            
            # Recalculate total
            total = Decimal('0.00')
            for item in items:
                total += Decimal(item['price']) * item['quantity']
            
            cart.items = items
            cart.total_amount = total
            cart.save()
            
            return Response({
                'success': True,
                'cart': {
                    'id': cart.id,
                    'items': cart.items,
                    'total_amount': cart.total_amount
                }
            }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to remove item: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
