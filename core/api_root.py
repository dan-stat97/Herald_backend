from rest_framework.decorators import api_view
from rest_framework.response import Response


def _url(request, path):
    return request.build_absolute_uri(f"/api/v1{path}")


@api_view(["GET"])
def api_root(request, format=None):
    """
    Lightweight API root.
    The browser docs page is the canonical endpoint reference.
    """
    return Response(
        {
            "message": "Welcome to Herald Backend API v1",
            "version": "1.0.0",
            "authentication": "JWT Bearer Token",
            "base_url": _url(request, "/"),
            "docs_html": _url(request, "/docs"),
            "docs_html_slash": _url(request, "/docs/"),
            "health": {
                "api": _url(request, "/health/"),
                "db": _url(request, "/health/db/"),
                "auth": _url(request, "/health/auth/"),
            },
            "search": {
                "users": _url(request, "/search/users/"),
                "posts": _url(request, "/search/posts/"),
                "unified": _url(request, "/search/"),
                "trending_topics": _url(request, "/trending/topics/"),
            },
            "notes": [
                "The full backend API reference is served at /api/v1/docs",
                "Use the docs page as the source of truth for routes",
                "Trailing slashes are optional on most endpoints, but both docs URLs are exposed here for clarity",
            ],
        }
    )
