from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from core.models import NewsArticle, NewsLike, NewsBookmark, Profiles


def _get_profile(request):
    """Return the core.Profiles record for the authenticated request user."""
    try:
        return Profiles.objects.get(user_id=request.user.id)
    except Profiles.DoesNotExist:
        return None


class NewsLikeView(APIView):
    """Like / unlike a news article."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, article_id):
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            article = NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

        like, created = NewsLike.objects.get_or_create(article=article, user=profile)
        if created:
            article.likes_count = (article.likes_count or 0) + 1
            article.save(update_fields=['likes_count'])

        return Response({
            'success': created,
            'message': 'Article liked' if created else 'Already liked',
            'likes_count': article.likes_count,
        })

    def delete(self, request, article_id):
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            article = NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = NewsLike.objects.filter(article=article, user=profile).delete()
        if deleted:
            article.likes_count = max(0, (article.likes_count or 1) - 1)
            article.save(update_fields=['likes_count'])

        return Response({
            'success': bool(deleted),
            'message': 'Article unliked' if deleted else 'Not liked yet',
            'likes_count': article.likes_count,
        })


class NewsBookmarkView(APIView):
    """Bookmark / remove bookmark from a news article."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, article_id):
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            article = NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

        _, created = NewsBookmark.objects.get_or_create(article=article, user=profile)
        return Response({
            'success': created,
            'message': 'Article bookmarked' if created else 'Already bookmarked',
        })

    def delete(self, request, article_id):
        profile = _get_profile(request)
        if not profile:
            return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            article = NewsArticle.objects.get(id=article_id)
        except NewsArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = NewsBookmark.objects.filter(article=article, user=profile).delete()
        return Response({
            'success': bool(deleted),
            'message': 'Bookmark removed' if deleted else 'Not bookmarked yet',
        })
