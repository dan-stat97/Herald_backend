from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Product, Order


class ProductViewSet(viewsets.ModelViewSet):
    """CRUD operations for products"""
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category')
        
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class ProductSerializer(serializers.ModelSerializer):
            class Meta:
                model = Product
                fields = ['id', 'name', 'description', 'category', 'price', 'image_url', 'created_at']
                read_only_fields = ['id', 'created_at']
        
        return ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """CRUD operations for orders"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        from users.models import User as UserProfile
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            return Order.objects.filter(user_id=profile)
        except UserProfile.DoesNotExist:
            return Order.objects.none()
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class OrderSerializer(serializers.ModelSerializer):
            username = serializers.CharField(source='user_id.username', read_only=True)
            
            class Meta:
                model = Order
                fields = ['id', 'user_id', 'username', 'items', 'total_amount', 'payment_type', 'status', 'created_at', 'completed_at']
                read_only_fields = ['id', 'user_id', 'created_at', 'completed_at']
        
        return OrderSerializer
    
    def perform_create(self, serializer):
        """Create order and process payment"""
        from users.models import User as UserProfile
        from wallets.models import Wallet
        from django.utils import timezone
        
        try:
            profile = UserProfile.objects.get(user_id=self.request.user)
            total_amount = serializer.validated_data['total_amount']
            payment_type = serializer.validated_data['payment_type']
            
            if payment_type == 'wallet':
                wallet = Wallet.objects.get(user_id=profile)
                
                if wallet.espees < total_amount:
                    from rest_framework.exceptions import ValidationError
                    raise ValidationError(f"Insufficient balance. Available: {wallet.espees}")
                
                wallet.espees -= total_amount
                wallet.save()
                
                serializer.save(
                    user_id=profile,
                    status='completed',
                    completed_at=timezone.now()
                )
            else:
                serializer.save(user_id=profile, status='pending')
                
        except UserProfile.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("User profile not found")
        except Wallet.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Wallet not found")
