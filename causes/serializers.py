from rest_framework import serializers
from .models import Cause, Donation


class DonationSerializer(serializers.ModelSerializer):
	donor_username = serializers.CharField(source='donor.username', read_only=True)
	donor_display_name = serializers.CharField(source='donor.display_name', read_only=True)
	donor_avatar_url = serializers.URLField(source='donor.avatar_url', read_only=True)
	donor_tier = serializers.CharField(source='donor.tier', read_only=True)

	class Meta:
		model = Donation
		fields = ['id', 'donor_username', 'donor_display_name', 'donor_avatar_url',
				  'donor_tier', 'amount', 'message', 'is_anonymous', 'created_at']
		read_only_fields = fields


class CauseSerializer(serializers.ModelSerializer):
	created_by_username = serializers.CharField(source='created_by.username', read_only=True)
	created_by_display_name = serializers.CharField(source='created_by.display_name', read_only=True)
	created_by_avatar_url = serializers.URLField(source='created_by.avatar_url', read_only=True)
	progress_percent = serializers.SerializerMethodField()
	donations_count = serializers.SerializerMethodField()
	is_donated = serializers.SerializerMethodField()

	class Meta:
		model = Cause
		fields = [
			'id', 'title', 'description', 'category',
			'created_by', 'created_by_username', 'created_by_display_name', 'created_by_avatar_url',
			'goal_amount', 'raised_amount', 'progress_percent',
			'donations_count', 'is_donated',
			'image_url', 'status', 'created_at', 'end_date',
		]
		read_only_fields = ['id', 'created_by', 'raised_amount', 'created_at']

	def get_progress_percent(self, obj):
		if obj.goal_amount and obj.goal_amount > 0:
			return round(float(obj.raised_amount) / float(obj.goal_amount) * 100, 1)
		return 0

	def get_donations_count(self, obj):
		return obj.donations.count()

	def get_is_donated(self, obj):
		request = self.context.get('request')
		if not request or not request.user.is_authenticated:
			return False
		try:
			from users.models import User as UserProfile
			profile = UserProfile.objects.get(user_id=request.user)
			return obj.donations.filter(donor=profile).exists()
		except Exception:
			return False
