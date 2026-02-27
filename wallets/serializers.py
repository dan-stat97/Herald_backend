from rest_framework import serializers
from .models import Wallet

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = [
            'id', 'user_id', 'httn_points', 'httn_tokens', 'espees', 'pending_rewards', 'created_at', 'updated_at'
        ]
        read_only_fields = fields
