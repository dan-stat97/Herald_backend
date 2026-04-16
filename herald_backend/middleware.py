import time

from django.urls import Resolver404, resolve


class OptionalSlashApiMiddleware:
    """
    Allow /api/... requests without a trailing slash to resolve against the
    slashed route when that route exists.

    This keeps the API friendly for clients while APPEND_SLASH remains False.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path_info = getattr(request, "path_info", "") or ""
        if path_info.startswith("/api/") and path_info != "/api/" and not path_info.endswith("/"):
            candidate = f"{path_info}/"
            try:
                resolve(candidate)
            except Resolver404:
                pass
            else:
                request.path_info = candidate
                request.path = candidate
                request.META["PATH_INFO"] = candidate

        return self.get_response(request)


class ApiTimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        if request.path.startswith('/api/'):
            try:
                response['X-Response-Time-ms'] = str(duration_ms)
            except Exception:
                pass

            content_length = None
            try:
                content_length = response.get('Content-Length')
            except Exception:
                content_length = None

            print(
                f"[API_TIMING] method={request.method} path={request.path} "
                f"status={getattr(response, 'status_code', 'unknown')} "
                f"duration_ms={duration_ms} content_length={content_length or '-'}"
            )

        return response
