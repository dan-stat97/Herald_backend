from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from core.models import NewsArticle, NewsLike, NewsBookmark
from users.models import User as UserProfile


class NewsLikeView(APIView):
    """Like a news article"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, article_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            article = NewsArticle.objects.get(id=article_id)
            
            # Check if already liked
            like, created = NewsLike.objects.get_or_create(
                article=article,
                user=profile
            )
            
            if created:
                article.likes_count += 1
                article.save()
                
                return Response({
                    'success': True,
                    'message': 'Article liked',
                    'likes_count': article.likes_count
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Already liked',
                    'likes_count': article.likes_count
                }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except NewsArticle.DoesNotExist:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to like article: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, article_id):
        """Unlike a news article"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            article = NewsArticle.objects.get(id=article_id)
            
            like = NewsLike.objects.filter(article=article, user=profile).first()
            
            if like:
                like.delete()
                article.likes_count = max(0, article.likes_count - 1)
                article.save()
                
                return Response({
                    'success': True,
                    'message': 'Article unliked',
                    'likes_count': article.likes_count
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Not liked yet',
                    'likes_count': article.likes_count
                }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except NewsArticle.DoesNotExist:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to unlike article: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NewsBookmarkView(APIView):
    """Bookmark a news article"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, article_id):
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            article = NewsArticle.objects.get(id=article_id)
            
            # Check if already bookmarked
            bookmark, created = NewsBookmark.objects.get_or_create(
                article=article,
                user=profile
            )
            
            if created:
                return Response({
                    'success': True,
                    'message': 'Article bookmarked'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Already bookmarked'
                }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except NewsArticle.DoesNotExist:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to bookmark article: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, article_id):
        """Remove bookmark from news article"""
        try:
            profile = UserProfile.objects.get(user_id=request.user)
            article = NewsArticle.objects.get(id=article_id)
            
            bookmark = NewsBookmark.objects.filter(article=article, user=profile).first()
            
            if bookmark:
                bookmark.delete()
                return Response({
                    'success': True,
                    'message': 'Bookmark removed'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': 'Not bookmarked yet'
                }, status=status.HTTP_200_OK)
            
        except UserProfile.DoesNotExist:
            return Response(
                {'error': 'User profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except NewsArticle.DoesNotExist:
            return Response(
                {'error': 'Article not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to remove bookmark: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
