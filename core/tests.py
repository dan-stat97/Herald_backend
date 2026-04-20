from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import NewsArticle
from posts.models import Post
from users.models import User


class ExploreSearchTests(TestCase):
    def setUp(self):
        auth_user = get_user_model().objects.create_user(
            username='exploretester',
            email='exploretester@example.com',
            password='password123',
        )
        self.profile = User.objects.create(
            user_id=auth_user,
            username='exploretester',
            display_name='Explore Tester',
            email='exploretester@example.com',
            onboarding_completed=True,
        )

    def test_unified_search_matches_underscore_topic_against_spaced_content(self):
        post = Post.objects.create(
            author_id=self.profile,
            content='Super Eagles delivered in Abuja and the whole city felt it. #sports #football',
            likes_count=18,
            comments_count=4,
            shares_count=2,
        )

        response = self.client.get('/api/v1/search/', {'q': 'super_eagles'})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(any(item['id'] == str(post.id) for item in payload['posts']))

    def test_explore_section_clusters_show_real_post_counts_for_story_topics(self):
        NewsArticle.objects.create(
            title='Super Eagles Qualify with Dominant Display in Abuja',
            source='Herald Sports',
            source_type='herald',
            content='Nigeria secured qualification in Abuja with a dominant display and supporters were electric.',
            category='sports super eagles abuja nigeria football',
            section='sports',
            likes_count=50,
        )
        Post.objects.create(
            author_id=self.profile,
            content='Super Eagles nights in Abuja always move the whole timeline. #super_eagles #abuja #sports',
            likes_count=25,
            comments_count=8,
            shares_count=5,
        )

        response = self.client.get('/api/v1/explore/sports/')

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['tab'], 'sports')
        self.assertTrue(payload['clusters'])
        self.assertTrue(any(cluster['posts_count'] > 0 for cluster in payload['clusters']))
