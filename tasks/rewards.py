from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core.leaderboard_cache import bump_leaderboard_cache_version
from tasks.models import RewardGrant, Task, UserTask
from wallets.models import Transaction, Wallet


ONBOARDING_TASKS = [
    {
        'code': 'first_post',
        'title': 'Create your first post',
        'description': 'Share your first post on Herald.',
        'task_type': 'campaign',
        'reward': 20,
        'target': 1,
    },
    {
        'code': 'join_3_conversations',
        'title': 'Join 3 conversations',
        'description': 'Write 3 thoughtful replies or comments.',
        'task_type': 'campaign',
        'reward': 25,
        'target': 3,
    },
    {
        'code': 'follow_2_people',
        'title': 'Follow 2 people',
        'description': 'Follow two people to improve your feed.',
        'task_type': 'campaign',
        'reward': 15,
        'target': 2,
    },
    {
        'code': 'join_first_community',
        'title': 'Join your first community',
        'description': 'Join a community to participate in shared conversations.',
        'task_type': 'campaign',
        'reward': 20,
        'target': 1,
    },
]

POST_MILESTONES = {
    'likes_count': (
        (5, 15, 'Your post reached 5 likes'),
        (10, 25, 'Your post reached 10 likes'),
        (25, 50, 'Your post reached 25 likes'),
    ),
    'comments_count': (
        (3, 15, 'Your post sparked 3 replies'),
        (10, 30, 'Your post sparked 10 replies'),
    ),
    'shares_count': (
        (3, 20, 'Your post was reposted 3 times'),
        (10, 40, 'Your post was reposted 10 times'),
    ),
}


def ensure_welcome_bonus(profile):
    return grant_points(
        profile,
        action_code='welcome_bonus',
        source_key='welcome',
        points=100,
        description='Welcome bonus',
    )


def ensure_default_tasks(profile):
    tasks = []
    for definition in ONBOARDING_TASKS:
        task, _ = Task.objects.get_or_create(
            code=definition['code'],
            defaults={
                'title': definition['title'],
                'description': definition['description'],
                'task_type': definition['task_type'],
                'reward': definition['reward'],
                'target': definition['target'],
            },
        )
        tasks.append(task)
        UserTask.objects.get_or_create(user=profile, task=task)
    return tasks


def increment_task_progress(profile, task_code: str, delta: int = 1):
    if delta <= 0:
        return None

    ensure_default_tasks(profile)
    task = Task.objects.filter(code=task_code).first()
    if not task:
        return None

    user_task, _ = UserTask.objects.get_or_create(user=profile, task=task)
    if user_task.completed:
        return user_task

    user_task.progress = min(task.target, (user_task.progress or 0) + delta)
    if user_task.progress >= task.target:
        user_task.completed = True
        user_task.completed_at = timezone.now()
        user_task.save(update_fields=['progress', 'completed', 'completed_at'])
    else:
        user_task.save(update_fields=['progress'])
    return user_task


def grant_points(profile, *, action_code: str, source_key: str, points: int, description: str, metadata=None, daily_cap: int | None = None):
    if points <= 0:
        return None

    if daily_cap is not None:
        today = timezone.now().date()
        today_count = RewardGrant.objects.filter(
            user=profile,
            action_code=action_code,
            created_at__date=today,
        ).count()
        if today_count >= daily_cap:
            return None

    with transaction.atomic():
        grant, created = RewardGrant.objects.get_or_create(
            user=profile,
            action_code=action_code,
            source_key=source_key,
            defaults={
                'points': points,
                'description': description,
                'metadata': metadata or {},
            },
        )
        if not created:
            return None

        wallet, _ = Wallet.objects.get_or_create(user_id=profile)
        Wallet.objects.filter(pk=wallet.pk).update(httn_points=F('httn_points') + points)
        Transaction.objects.create(
            wallet_id=wallet,
            transaction_type='reward',
            amount=Decimal(points),
            currency='points',
            description=description,
        )

    bump_leaderboard_cache_version()
    return grant


def award_post_creation(profile, post):
    increment_task_progress(profile, 'first_post')
    return grant_points(
        profile,
        action_code='post_create',
        source_key=str(post.id),
        points=25,
        description='Created a post',
        metadata={'post_id': str(post.id)},
    )


def award_comment_creation(profile, comment):
    increment_task_progress(profile, 'join_3_conversations')
    return grant_points(
        profile,
        action_code='comment_create',
        source_key=str(comment.id),
        points=10,
        description='Joined a conversation',
        metadata={'comment_id': str(comment.id), 'post_id': str(comment.post_id)},
        daily_cap=5,
    )


def record_follow_action(profile, followed_profile):
    increment_task_progress(profile, 'follow_2_people')
    return followed_profile


def record_community_join(profile, community):
    increment_task_progress(profile, 'join_first_community')
    return community


def award_post_engagement_milestones(post, metric: str, count: int):
    milestones = POST_MILESTONES.get(metric, ())
    if not milestones:
        return

    for threshold, points, description in milestones:
        if count < threshold:
            continue
        grant_points(
            post.author_id,
            action_code=f'post_{metric}_milestone',
            source_key=f'{post.id}:{metric}:{threshold}',
            points=points,
            description=description,
            metadata={'post_id': str(post.id), 'metric': metric, 'threshold': threshold},
        )


def claim_user_task_reward(profile, task_id):
    ensure_default_tasks(profile)
    user_task = UserTask.objects.select_related('task').filter(id=task_id, user=profile).first()
    if not user_task:
        return None, {'error': 'Task not found'}, 404
    if not user_task.completed:
        return None, {'error': 'Task not completed yet'}, 400
    if user_task.claimed:
        return None, {'error': 'Reward already claimed'}, 400

    wallet, _ = Wallet.objects.get_or_create(user_id=profile)
    with transaction.atomic():
        Wallet.objects.filter(pk=wallet.pk).update(httn_points=F('httn_points') + user_task.task.reward)
        Transaction.objects.create(
            wallet_id=wallet,
            transaction_type='reward',
            amount=Decimal(user_task.task.reward),
            currency='points',
            description=f'Task reward: {user_task.task.title}',
        )
        user_task.claimed = True
        user_task.save(update_fields=['claimed'])

    wallet.refresh_from_db(fields=['httn_points'])
    bump_leaderboard_cache_version()
    return user_task, {
        'success': True,
        'reward': user_task.task.reward,
        'new_balance': wallet.httn_points,
    }, 200
