from django.core.cache import cache


def get_leaderboard_cache_version() -> int:
    key = 'leaderboard:version'
    version = cache.get(key)
    if version is None:
        version = 1
        cache.set(key, version, 60 * 60)
    return int(version)


def bump_leaderboard_cache_version() -> int:
    key = 'leaderboard:version'
    try:
        return int(cache.incr(key))
    except ValueError:
        version = 2
        cache.set(key, version, 60 * 60)
        return version
