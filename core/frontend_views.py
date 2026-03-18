import re
from collections import Counter

from django.db import connection
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Post
from posts.serializers import PostSerializer
from core.pagination import StandardPagination


class ApiHealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ApiHealthDbView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return Response({"status": "ok", "database": "connected"})
        except Exception as exc:
            return Response({"status": "error", "database": str(exc)}, status=500)


class ApiHealthAuthView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok", "authenticated": True, "user_id": request.user.id})


class TrendingTopicsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 100)
        posts = Post.objects.order_by("-created_at").values_list("content", flat=True)[:1000]

        hashtag_pattern = re.compile(r"#([A-Za-z0-9_]+)")
        counter = Counter()

        for content in posts:
            if not content:
                continue
            tags = hashtag_pattern.findall(content)
            counter.update(tag.lower() for tag in tags)

        data = [{"topic": topic, "count": count} for topic, count in counter.most_common(limit)]
        return Response(data)


class SearchPostsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get("q") or request.query_params.get("query")
        if not query:
            return Response({"data": [], "pagination": {"page": 1, "limit": 20, "total": 0, "total_pages": 0}})

        queryset = Post.objects.filter(content__icontains=query).select_related("author_id", "author_id__user_id").order_by("-created_at")
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = PostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
