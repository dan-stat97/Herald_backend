from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user_id', 'httn_points', 'httn_tokens', 'espees', 'pending_rewards', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_id(self, obj):
        """Return the UUID of the user profile"""
        try:
            return str(obj.user_id.id) if obj.user_id else None
        except:
            return None
