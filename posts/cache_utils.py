from django.core.cache import cache


POST_TIMELINE_CACHE_VERSION_KEY = 'posts:timeline-cache-version'


def get_post_timeline_cache_version() -> int:
    version = cache.get(POST_TIMELINE_CACHE_VERSION_KEY)
    if version is None:
        version = 1
        cache.set(POST_TIMELINE_CACHE_VERSION_KEY, version, None)
    return int(version)


def bump_post_timeline_cache_version() -> int:
    try:
        return int(cache.incr(POST_TIMELINE_CACHE_VERSION_KEY))
    except Exception:
        next_version = get_post_timeline_cache_version() + 1
        cache.set(POST_TIMELINE_CACHE_VERSION_KEY, next_version, None)
        return next_version
