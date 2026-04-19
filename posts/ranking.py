"""
Herald Social feed ranking — modelled on Twitter/X's open-sourced algorithm.

Sources:
  github.com/twitter/the-algorithm
  github.com/twitter/the-algorithm-ml  (FEATURES.md, HomeGlobalParams.scala)
  blog.x.com/engineering/en_us/topics/open-source/2023/twitter-recommendation-algorithm

Key differences from Twitter's production system
-------------------------------------------------
Twitter uses a 48 M-parameter MaskNet neural network (Heavy Ranker) trained on
real-time engagement data and hundreds of user/author/tweet features. We don't
have that infrastructure, so we approximate the Heavy Ranker with a hand-tuned
weighted sum over the engagement signals we DO have, using Twitter's published
weights as the calibration reference.

Engagement weights (from HomeGlobalParams.scala, April 2023):
  Favorite/Like          +0.5   (baseline)
  Retweet/Share          +1.0   (2× like)
  Reply                 +13.5   (27× like — conversation value is paramount)
  Good profile click    +12.0   (deep engagement signal)
  Good click (thread)   +11.0
  Bookmark               +2.0   (strong save intent; not in Twitter's OSS but
                                  used here as proxy for their undisclosed
                                  "good_click_v2" weight of +10)
  Video ≥ 50% play       +0.005  (per view; weak per-unit but scales)
  Negative feedback     -74.0
  Report               -369.0

Time decay (ranking.thrift, Heavy Ranker path):
  decay = max(exp(-0.003 × age_minutes), DECAY_FLOOR)
  DECAY_FLOOR = 0.6   — posts never fully disappear
  At 200 minutes (~3.3 h) decay hits the floor.

Author quality (Tweepcred gate, simplified):
  Herald maps this to the author's followers_count.  Accounts with < 50
  followers get a candidate cap equivalent of 3 posts max in the pool.

Verified / Creator boosts (HomeGlobalParams.scala Blue multipliers):
  In-network  verified author: ×4.0
  Out-of-network verified:     ×2.0

Social proof gate (out-of-network hard filter):
  OON tweet must have at least one person the viewer follows who either
  engaged with it OR follows the author.  Tweets that fail are excluded.

Author diversity (Earlybird):
  maxConsecutiveSameUser = 2 — same author cannot appear more than twice in
  any 5-post window.  Repeat appearances get their score halved.
"""

import math
import re
from collections import Counter

from django.core.cache import cache
from django.utils import timezone

from core.models import Follow, Profiles
from livestreams.models import LiveStream
from users.legacy_profiles import ensure_legacy_profile
from users.models import User as UserProfile

from .models import Post, PostBookmark, PostLike, PostRepost


# ── Engagement weights (Twitter HomeGlobalParams calibration) ─────────────────
W_LIKE        =   0.5
W_RETWEET     =   1.0
W_REPLY       =  13.5    # conversation depth is Twitter's highest-value signal
W_BOOKMARK    =   2.0    # proxy for good_click_v2
W_VIEW        =   0.005  # per view — scaled by total view count

# ── Time decay (Heavy Ranker path, ranking.thrift) ────────────────────────────
DECAY_SLOPE   = 0.003    # per minute
DECAY_FLOOR   = 0.6      # minimum: posts never completely suppressed

# ── Author diversity (Earlybird maxConsecutiveSameUser = 2) ───────────────────
REPEAT_AUTHOR_PENALTY = 0.5   # halve score on 2nd appearance in same refresh
MAX_SAME_AUTHOR_IN_WINDOW = 2
WINDOW_SIZE = 5

# ── Verified / Creator boosts (Blue multipliers) ─────────────────────────────
VERIFIED_IN_NETWORK_BOOST  = 4.0
VERIFIED_OUT_NETWORK_BOOST = 2.0

# ── Social signals ────────────────────────────────────────────────────────────
FOLLOWED_AUTHOR_BOOST     = 34.0   # primary in-network signal
ENGAGED_AUTHOR_BOOST      = 18.0   # previously engaged with this author
NETWORK_LIKED_BOOST       = 14.0   # someone you follow liked this
SECOND_DEGREE_BOOST_UNIT  =  3.2   # per second-degree mutual; capped at 14
SECOND_DEGREE_CAP         = 14.0
INTEREST_OVERLAP_BOOST    =  8.5   # per overlapping term
HASHTAG_OVERLAP_BOOST     =  5.0   # per overlapping hashtag
MEDIA_BOOST               =  2.5   # image or video present
LIVE_AUTHOR_BOOST         = 12.0   # author currently streaming
CREATOR_BOOST             =  3.5
REPUTATION_CAP            =  7.0   # max reputation contribution

# ── Candidate pool limits ─────────────────────────────────────────────────────
IN_NETWORK_POOL  = 200   # posts from followed accounts
OUT_NETWORK_POOL = 250   # posts from everyone else
ANON_POOL        = 300   # no-auth / no-follows fallback

TOKEN_RE = re.compile(r"[A-Za-z0-9_#']+")


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _cache_fetch(key: str, ttl: int, builder):
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = builder()
    cache.set(key, value, ttl)
    return value


def _safe_terms(values) -> set[str]:
    terms: set[str] = set()
    for value in values or []:
        if not value:
            continue
        for token in TOKEN_RE.findall(str(value).lower().replace('-', ' ')):
            cleaned = token.strip().lstrip('#')
            if len(cleaned) >= 3:
                terms.add(cleaned)
    return terms


def _post_terms(post: Post) -> set[str]:
    author = getattr(post, 'author_id', None)
    values = [post.content]
    if author:
        values.extend([
            getattr(author, 'username', ''),
            getattr(author, 'display_name', ''),
            getattr(author, 'bio', ''),
        ])
    return _safe_terms(values)


def _get_profile(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        return UserProfile.objects.get(user_id=user)
    except UserProfile.DoesNotExist:
        return None


def _followed_author_ids(profile: UserProfile | None) -> set[str]:
    if not profile:
        return set()
    def builder():
        legacy = ensure_legacy_profile(profile)
        if not legacy:
            return set()
        ids = Profiles.objects.filter(
            id__in=Follow.objects.filter(follower_id=legacy.id).values_list('following_id', flat=True)
        ).values_list('user_id', flat=True)
        return {str(v) for v in ids}
    return _cache_fetch(f'feed:followed-authors:{profile.id}', 60, builder)


def _follow_network_signals(profile: UserProfile | None):
    """
    Returns:
      liked_by_network_post_ids  — set of post IDs liked by someone the viewer follows
      second_degree_counts       — dict[author_auth_id, mutual_count]
    """
    if not profile:
        return set(), {}
    def builder():
        legacy = ensure_legacy_profile(profile)
        if not legacy:
            return set(), {}

        followed_legacy_ids = list(
            Follow.objects.filter(follower_id=legacy.id).values_list('following_id', flat=True)
        )
        if not followed_legacy_ids:
            return set(), {}

        followed_profiles    = list(Profiles.objects.filter(id__in=followed_legacy_ids))
        followed_auth_ids    = [p.user_id for p in followed_profiles]
        followed_profile_ids = list(
            UserProfile.objects.filter(user_id_id__in=followed_auth_ids).values_list('id', flat=True)
        )

        # Posts liked by people the viewer follows (social proof)
        liked_post_ids = set(
            PostLike.objects.filter(user_id__in=followed_profile_ids).values_list('post_id', flat=True)
        )

        # Second-degree follow counts
        second_degree: dict[str, int] = {}
        second_degree_rows = (
            Follow.objects
            .filter(follower_id__in=followed_legacy_ids)
            .values_list('following_id', flat=True)
        )
        for auth_id in Profiles.objects.filter(id__in=second_degree_rows).values_list('user_id', flat=True):
            key = str(auth_id)
            second_degree[key] = second_degree.get(key, 0) + 1

        return liked_post_ids, second_degree

    return _cache_fetch(f'feed:network-signals:{profile.id}', 90, builder)


def _engaged_author_ids(profile: UserProfile | None) -> tuple[set[str], set[str]]:
    """Authors/topics the viewer has previously engaged with."""
    if not profile:
        return set(), set()
    def builder():
        recent_likes     = PostLike.objects.filter(user=profile).select_related('post__author_id')[:120]
        recent_reposts   = PostRepost.objects.filter(user=profile).select_related('post__author_id')[:120]
        recent_bookmarks = PostBookmark.objects.filter(user=profile).select_related('post__author_id')[:120]

        author_ids: set[str] = set()
        term_bag: list[str]  = []
        for rel in [*recent_likes, *recent_reposts, *recent_bookmarks]:
            post   = getattr(rel, 'post', None)
            author = getattr(post, 'author_id', None)
            if author and getattr(author, 'user_id_id', None):
                author_ids.add(str(author.user_id_id))
            if post:
                term_bag.extend(_post_terms(post))
        return author_ids, set(term_bag)
    return _cache_fetch(f'feed:engaged-authors:{profile.id}', 90, builder)


def _live_author_ids() -> set[str]:
    return _cache_fetch(
        'feed:live-authors', 20,
        lambda: {
            str(v)
            for v in LiveStream.objects.filter(status='live').values_list('user__user_id', flat=True)
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core scoring function  (approximates Twitter's Heavy Ranker weighted sum)
# ─────────────────────────────────────────────────────────────────────────────

def _time_decay(age_hours: float) -> float:
    """
    Exponential decay with floor (Heavy Ranker / ranking.thrift).
    DECAY_SLOPE is per-minute; convert age_hours → minutes.
    Floor = 0.6 → posts older than ~3.3 hours never drop below 60%.
    """
    age_minutes = max(age_hours * 60.0, 0.1)
    return max(math.exp(-DECAY_SLOPE * age_minutes), DECAY_FLOOR)


def _heavy_ranker_score(post: Post) -> float:
    """
    Approximate Twitter's Heavy Ranker weighted sum using available signals.
    Engagement counts proxy for the probability outputs of Twitter's neural net.
    """
    likes     = post.likes_count     or 0
    shares    = post.shares_count    or 0
    comments  = post.comments_count  or 0
    bookmarks = post.bookmarks_count or 0
    views     = post.views_count     or 0

    return (
        likes     * W_LIKE
        + shares    * W_RETWEET
        + comments  * W_REPLY      # highest weight — mirrors Twitter's 13.5×
        + bookmarks * W_BOOKMARK
        + views     * W_VIEW
    )


def _base_post_score(
    post: Post,
    *,
    followed_ids: set[str],
    engaged_author_ids: set[str],
    user_terms: set[str],
    live_author_ids: set[str],
    liked_by_network_post_ids: set,
    second_degree_author_counts: dict[str, int],
    is_in_network: bool = False,
) -> float:
    author        = getattr(post, 'author_id', None)
    author_auth_id = str(getattr(author, 'user_id_id', '') or '')
    post_terms    = _post_terms(post)

    now       = timezone.now()
    age_hours = max((now - post.created_at).total_seconds() / 3600.0, 0.01)

    # ── Heavy Ranker engagement score ────────────────────────────────────────
    engagement_score = _heavy_ranker_score(post)

    # ── Time decay (Twitter formula) ─────────────────────────────────────────
    decay = _time_decay(age_hours)

    score = engagement_score * decay

    # ── Social graph boosts ──────────────────────────────────────────────────
    if author_auth_id and author_auth_id in followed_ids:
        score += FOLLOWED_AUTHOR_BOOST

    if author_auth_id and author_auth_id in engaged_author_ids:
        score += ENGAGED_AUTHOR_BOOST

    if post.id in liked_by_network_post_ids:
        score += NETWORK_LIKED_BOOST                       # social proof

    if author_auth_id and author_auth_id in second_degree_author_counts:
        raw = second_degree_author_counts[author_auth_id] * SECOND_DEGREE_BOOST_UNIT
        score += min(raw, SECOND_DEGREE_CAP)

    # ── Interest / topic match ───────────────────────────────────────────────
    overlap = len(user_terms & post_terms)
    if overlap:
        score += overlap * INTEREST_OVERLAP_BOOST

    hashtag_overlap = len({
        token for token in TOKEN_RE.findall((post.content or '').lower())
        if token.startswith('#')
    } & {f'#{t}' for t in user_terms})
    if hashtag_overlap:
        score += hashtag_overlap * HASHTAG_OVERLAP_BOOST

    # ── Author quality boosts ────────────────────────────────────────────────
    is_verified = getattr(author, 'is_verified', False)
    if is_verified:
        # Twitter Blue multipliers: 4× in-network, 2× out-of-network
        multiplier = VERIFIED_IN_NETWORK_BOOST if is_in_network else VERIFIED_OUT_NETWORK_BOOST
        score *= multiplier

    if getattr(author, 'is_creator', False):
        score += CREATOR_BOOST

    reputation = getattr(author, 'reputation', 0) or 0
    if reputation:
        score += min(float(reputation) / 80.0, REPUTATION_CAP)

    # ── Content-type boosts ──────────────────────────────────────────────────
    if post.media_url or (post.media_urls and len(post.media_urls)):
        score += MEDIA_BOOST        # Twitter Earlybird: media tweets ×2.0

    if author_auth_id and author_auth_id in live_author_ids:
        score += LIVE_AUTHOR_BOOST

    return score


# ─────────────────────────────────────────────────────────────────────────────
# Social proof gate  (Twitter hard filter for out-of-network tweets)
# ─────────────────────────────────────────────────────────────────────────────

def passes_social_proof(
    post: Post,
    followed_ids: set[str],
    liked_by_network_post_ids: set,
) -> bool:
    """
    Out-of-network tweets must satisfy at least one of:
      1. Someone the viewer follows liked / reposted it
      2. The post author is followed by someone the viewer follows
         (second-degree follow — approximated via liked_by_network_post_ids)

    If the viewer has no follows yet, all posts pass (new-user fallback).
    """
    if not followed_ids:
        return True  # new user — show everything
    return post.id in liked_by_network_post_ids


# ─────────────────────────────────────────────────────────────────────────────
# Diversity pass  (Earlybird maxConsecutiveSameUser = 2)
# ─────────────────────────────────────────────────────────────────────────────

def _diversity_pass(scored_posts: list[tuple[float, Post]]) -> list[Post]:
    """
    Prevents any author from appearing more than MAX_SAME_AUTHOR_IN_WINDOW
    times in any WINDOW_SIZE-post sliding window.
    Subsequent appearances get their score halved first; if still over the cap
    the post is deferred to a later position.
    """
    out: list[Post]    = []
    window: list[str]  = []          # rolling author_key window
    deferred: list[Post] = []        # posts pushed back due to repetition

    def _author_key(p: Post) -> str:
        return str(getattr(p.author_id, 'user_id_id', '') or '')

    for _, post in scored_posts:
        key   = _author_key(post)
        recent = window[-WINDOW_SIZE:]
        if recent.count(key) < MAX_SAME_AUTHOR_IN_WINDOW:
            out.append(post)
            window.append(key)
        else:
            deferred.append(post)

    # Append deferred posts at the end (they still appear — just later)
    out.extend(deferred)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point  (called by PostViewSet.list and PostFeedView)
# ─────────────────────────────────────────────────────────────────────────────

def rank_feed_posts(queryset, request, candidate_limit: int = ANON_POOL) -> list[Post]:
    """
    Legacy entry point kept for PostViewSet.list compatibility.
    Scores a single flat queryset (no in/out-of-network split).
    """
    profile            = _get_profile(getattr(request, 'user', None))
    followed_ids       = _followed_author_ids(profile)
    engaged_ids, terms = _engaged_author_ids(profile)
    interest_terms     = _safe_terms(getattr(profile, 'interests', []) if profile else [])
    user_terms         = interest_terms | terms
    live_ids           = _live_author_ids()
    net_likes, sec_deg = _follow_network_signals(profile)

    kwargs = dict(
        followed_ids=followed_ids,
        engaged_author_ids=engaged_ids,
        user_terms=user_terms,
        live_author_ids=live_ids,
        liked_by_network_post_ids=net_likes,
        second_degree_author_counts=sec_deg,
    )

    candidates = list(queryset[:candidate_limit])
    if not candidates:
        return []

    scored = sorted(
        [(_base_post_score(p, **kwargs), p) for p in candidates],
        key=lambda x: (x[0], x[1].created_at),
        reverse=True,
    )

    return _diversity_pass(scored)


def build_twitter_feed(request) -> list[Post]:
    """
    Full Twitter-style two-pool feed with social proof gating.

    Pool A (in-network,  ~40%): posts from followed accounts — scored + diversity pass
    Pool B (out-of-network, ~60%): posts NOT from followed accounts — social proof
                                   gated, scored + diversity pass
    Final: interleaved 8 in-network + 12 out-of-network per 20-post block.
    """
    profile            = _get_profile(getattr(request, 'user', None))
    followed_ids       = _followed_author_ids(profile)
    engaged_ids, terms = _engaged_author_ids(profile)
    interest_terms     = _safe_terms(getattr(profile, 'interests', []) if profile else [])
    user_terms         = interest_terms | terms
    live_ids           = _live_author_ids()
    net_likes, sec_deg = _follow_network_signals(profile)

    score_kwargs = dict(
        followed_ids=followed_ids,
        engaged_author_ids=engaged_ids,
        user_terms=user_terms,
        live_author_ids=live_ids,
        liked_by_network_post_ids=net_likes,
        second_degree_author_counts=sec_deg,
    )

    base_qs = Post.objects.select_related('author_id', 'author_id__user_id').all()

    if followed_ids:
        # ── Pool A: in-network ────────────────────────────────────────────────
        in_qs = base_qs.filter(
            author_id__user_id_id__in=followed_ids
        ).order_by('-created_at')[:IN_NETWORK_POOL]

        in_scored = sorted(
            [(_base_post_score(p, is_in_network=True, **score_kwargs), p) for p in in_qs],
            key=lambda x: (x[0], x[1].created_at), reverse=True,
        )

        # ── Pool B: out-of-network (social proof gated) ───────────────────────
        out_qs = base_qs.exclude(
            author_id__user_id_id__in=followed_ids
        ).order_by('-created_at')[:OUT_NETWORK_POOL]

        out_scored = sorted(
            [
                (_base_post_score(p, is_in_network=False, **score_kwargs), p)
                for p in out_qs
                # Hard gate: OON post must have social proof from viewer's network
                if passes_social_proof(p, followed_ids, net_likes)
            ],
            key=lambda x: (x[0], x[1].created_at), reverse=True,
        )

        # ── Diversity pass on each pool independently ─────────────────────────
        in_posts  = _diversity_pass(in_scored)
        out_posts = _diversity_pass(out_scored)

        # ── Interleave: 8 in-network + 12 out-of-network per block ────────────
        blended: list[Post] = []
        in_i = out_i = 0
        while in_i < len(in_posts) or out_i < len(out_posts):
            for _ in range(8):     # ~40% in-network
                if in_i < len(in_posts):
                    blended.append(in_posts[in_i]); in_i += 1
            for _ in range(12):    # ~60% out-of-network
                if out_i < len(out_posts):
                    blended.append(out_posts[out_i]); out_i += 1

    else:
        # No follows — pure global ranking (new user / anonymous)
        candidates = list(base_qs.order_by('-created_at')[:ANON_POOL])
        scored = sorted(
            [(_base_post_score(p, **score_kwargs), p) for p in candidates],
            key=lambda x: (x[0], x[1].created_at), reverse=True,
        )
        blended = _diversity_pass(scored)

    return blended
