from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from users.models import User as UserProfile
from core.models import Follow

class FollowApiTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', email='user1@example.com', password='pass1234')
        self.user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass1234')
        self.profile1 = UserProfile.objects.create(user_id=self.user1, username='user1', display_name='User 1')
        self.profile2 = UserProfile.objects.create(user_id=self.user2, username='user2', display_name='User 2')
        self.client.login(username='user1', password='pass1234')

    def test_follow_user(self):
        url = reverse('user-follow', kwargs={'pk': self.profile2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Follow.objects.filter(follower_id=self.profile1.id, following_id=self.profile2.id).exists())

    def test_unfollow_user(self):
        Follow.objects.create(follower_id=self.profile1.id, following_id=self.profile2.id)
        url = reverse('user-unfollow', kwargs={'pk': self.profile2.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Follow.objects.filter(follower_id=self.profile1.id, following_id=self.profile2.id).exists())

    def test_followers_list(self):
        Follow.objects.create(follower_id=self.profile1.id, following_id=self.profile2.id)
        url = reverse('user-followers', kwargs={'pk': self.profile2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user1')

    def test_following_list(self):
        Follow.objects.create(follower_id=self.profile1.id, following_id=self.profile2.id)
        url = reverse('user-following', kwargs={'pk': self.profile1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['username'], 'user2')
