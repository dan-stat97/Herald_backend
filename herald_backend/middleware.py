import time


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
