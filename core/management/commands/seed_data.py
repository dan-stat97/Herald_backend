"""
Management command: seed_data

Seeds official Herald newsroom-style users, posts, and news articles so the
X-like clustered news page has real data to work with.

The command is intentionally idempotent:
- users are created once and then reused
- posts are keyed by (author, content)
- articles are keyed by title

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear
    python manage.py seed_data --skip-posts
    python manage.py seed_data --skip-news
"""

from datetime import timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import NewsArticle
from posts.models import Post
from users.models import User as UserProfile

AuthUser = get_user_model()


def article_source(category: str) -> str:
    category = (category or "").lower()
    if "loveworld" in category:
        return "Loveworld"
    if "healing" in category:
        return "Healing School"
    if "external" in category or "christian" in category:
        return "External"
    return "Herald Social"

OFFICIAL_USERS = [
    {
        "username": "heraldnews",
        "display_name": "Herald News",
        "bio": "Official Herald Social newsroom covering faith, culture, and events shaping the body of Christ.",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "heraldworlddesk",
        "display_name": "Herald World Desk",
        "bio": "Official Herald desk tracking missions, world evangelism, and global Christian impact stories.",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "heraldprayerdesk",
        "display_name": "Herald Prayer Desk",
        "bio": "Official Herald prayer desk covering prayer movements, testimonies, and revival moments.",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "heraldworship",
        "display_name": "Herald Worship",
        "bio": "Official Herald worship desk for gospel music, worship culture, and live ministry moments.",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "heraldtoday",
        "display_name": "Herald Today",
        "bio": "Official Herald desk connecting technology, society, health, and national headlines to faith conversations.",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "heraldsports",
        "display_name": "Herald Sports",
        "bio": "Official Herald sports desk covering major moments, resilience stories, and what people are talking about now.",
        "tier": "creator",
        "is_verified": True,
    },
]

STORY_PACKETS = [
    {
        "username": "heraldprayerdesk",
        "article": {
            "title": "Church Leaders Across Nigeria Unite for National Prayer Summit",
            "content": (
                "Church leaders from across Nigeria gathered in Abuja for a major prayer summit focused on national "
                "intercession, peace, economic recovery, and the spiritual health of the nation. Organisers described "
                "it as one of the strongest cross-denominational prayer gatherings in recent years."
            ),
            "category": "faith prayer summit abuja nigeria",
            "image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800",
            "source_url": "https://heraldsocial.app/news/prayer-summit-nigeria",
            "likes_count": 186,
        },
        "posts": [
            "Abuja is still buzzing after the national prayer summit. The atmosphere of unity, intercession, and expectation was undeniable. #prayer #summit #abuja #faith",
            "When pastors, leaders, and believers lift one voice for a nation, the conversation changes. Prayer summit moments like this matter. #nigeria #prayer #church",
        ],
    },
    {
        "username": "heraldtoday",
        "article": {
            "title": "Tech Startup Ecosystem in Lagos Records Major Growth This Quarter",
            "content": (
                "Lagos continues to strengthen its position as a leading African tech city, with startup growth driven by "
                "fintech, healthtech, and digital services. Analysts say stronger investor confidence and better infrastructure "
                "are helping the ecosystem mature."
            ),
            "category": "technology lagos startup fintech innovation",
            "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
            "source_url": "https://heraldsocial.app/news/lagos-tech-growth",
            "likes_count": 142,
        },
        "posts": [
            "Lagos tech keeps proving why it is one of the biggest innovation conversations in Africa right now. Startup builders are moving with real momentum. #lagos #technology #startup",
            "The strongest tech ecosystems are built on talent, execution, and trust. Lagos is showing all three in this season. #innovation #fintech #lagos",
        ],
    },
    {
        "username": "heraldworlddesk",
        "article": {
            "title": "Herald Social Prayer Drive Unites Thousands Across Africa",
            "content": (
                "Thousands of users across multiple African nations joined Herald Social's coordinated prayer drive, sharing "
                "testimonies, requests, and live encouragement. Organisers say the response confirms a growing hunger for "
                "digital faith communities that strengthen real-world prayer and evangelism."
            ),
            "category": "world evangelism africa prayer herald social",
            "image_url": "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?w=800",
            "source_url": "https://heraldsocial.app/news/herald-prayer-drive-africa",
            "likes_count": 231,
        },
        "posts": [
            "What happens when believers across Africa move in one stream of prayer? We saw it this week on Herald Social. #africa #prayer #worldevangelism",
            "This is why digital faith communities matter: prayer requests, testimonies, outreach, and world evangelism all meeting in one place. #heraldsocial #evangelism #africa",
        ],
    },
    {
        "username": "heraldworship",
        "article": {
            "title": "New Gospel Album Breaks Streaming Records Across Africa",
            "content": (
                "A major new gospel release has broken streaming records across the continent, becoming one of the fastest-rising "
                "worship projects of the year. Worship leaders say the songs are already shaping church setlists and prayer meetings."
            ),
            "category": "gospel music worship africa streaming",
            "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
            "source_url": "https://heraldsocial.app/news/gospel-album-streaming-records",
            "likes_count": 167,
        },
        "posts": [
            "You can tell when a worship project carries more than good production. This one is landing in churches fast. #gospel #music #worship",
            "Streaming numbers matter because they point to real hunger. People are carrying these songs into prayer rooms and services. #worship #africa #gospelmusic",
        ],
    },
    {
        "username": "heraldsports",
        "article": {
            "title": "Super Eagles Qualify with Dominant Display in Abuja",
            "content": (
                "Nigeria secured qualification with a convincing performance in Abuja, giving supporters another major sports moment "
                "to celebrate. Analysts praised the team's discipline, finishing, and crowd energy."
            ),
            "category": "sports super eagles abuja nigeria football",
            "image_url": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=800",
            "source_url": "https://heraldsocial.app/news/super-eagles-abuja",
            "likes_count": 154,
        },
        "posts": [
            "Abuja was loud and the Super Eagles gave supporters something real to celebrate. Big night for Nigerian football. #sports #supereagles #abuja",
            "There are wins that feel routine and then there are wins that reset momentum. This one felt important. #football #nigeria #sports",
        ],
    },
    {
        "username": "heraldtoday",
        "article": {
            "title": "Cybersecurity Alert Warns Customers About New Phishing Scam",
            "content": (
                "Authorities have warned customers about a new phishing campaign using fake bank messages and login prompts. "
                "People are being advised to avoid suspicious links and access financial services only through verified channels."
            ),
            "category": "technology cybersecurity phishing banks nigeria",
            "image_url": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800",
            "source_url": "https://heraldsocial.app/news/phishing-alert-nigeria",
            "likes_count": 118,
        },
        "posts": [
            "Important reminder: urgency is one of the biggest phishing tricks. Slow down before you tap that bank message. #cybersecurity #phishing #nigeria",
            "The strongest digital habit right now might be simple: do not trust random links with your finances. #technology #security #banks",
        ],
    },
    {
        "username": "heraldnews",
        "article": {
            "title": "Youth Ministry Conference Draws Record Turnout in Lagos",
            "content": (
                "A major youth ministry conference in Lagos recorded a massive turnout, blending worship, discipleship, leadership, "
                "and practical life conversations. Organisers described the response as a sign of strong spiritual hunger among young adults."
            ),
            "category": "faith youth ministry lagos conference",
            "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
            "source_url": "https://heraldsocial.app/news/youth-conference-lagos",
            "likes_count": 173,
        },
        "posts": [
            "The scale of conversation around the Lagos youth ministry conference says a lot about this moment. Young believers want depth and direction. #youth #ministry #lagos #faith",
            "This generation is not short on passion. The real story is how many young people are showing up hungry for truth and purpose. #conference #church #youth",
        ],
    },
    {
        "username": "heraldworlddesk",
        "article": {
            "title": "Free Online Bible College Expands Access to Ministry Training",
            "content": (
                "A free online Bible college has opened theological training to thousands of learners across regions that would not "
                "normally have easy access to structured ministry education. Leaders say this kind of access can accelerate discipleship and outreach."
            ),
            "category": "education bible college ministry training evangelism",
            "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800",
            "source_url": "https://heraldsocial.app/news/online-bible-college",
            "likes_count": 126,
        },
        "posts": [
            "Training multiplies impact. When ministry education becomes easier to access, evangelism and discipleship can scale faster. #biblecollege #training #evangelism",
            "One of the most practical ways to strengthen world evangelism is to remove barriers to sound Bible training. #education #ministry #worldevangelism",
        ],
    },
    {
        "username": "heraldtoday",
        "article": {
            "title": "Maternal Health Initiative Launches in 10 States",
            "content": (
                "A new maternal health initiative is expanding access to antenatal care, safe delivery support, and postnatal services "
                "in high-need regions. Health advocates say consistent follow-through will be critical to long-term impact."
            ),
            "category": "health maternal care nigeria",
            "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800",
            "source_url": "https://heraldsocial.app/news/maternal-health-initiative",
            "likes_count": 111,
        },
        "posts": [
            "Health stories deserve the same attention as headline politics. Maternal care changes entire families and communities. #health #maternalcare #nigeria",
            "The real test for any health initiative is follow-through. Access, staffing, and trust all have to move together. #publichealth #care #health",
        ],
    },
    {
        "username": "heraldnews",
        "article": {
            "title": "Gen Z Is Reshaping Church Culture Through Authentic Community",
            "content": (
                "A new generation of church members is pushing communities toward greater authenticity, practical discipleship, and "
                "honest conversation. Observers say the shift is changing how churches think about belonging, leadership, and mission."
            ),
            "category": "faith gen z church culture community",
            "image_url": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800",
            "source_url": "https://heraldsocial.app/news/gen-z-church-culture",
            "likes_count": 134,
        },
        "posts": [
            "Gen Z is not asking for less church. They are asking for real discipleship, honest community, and visible purpose. #genz #church #community",
            "Church culture is strongest when truth and authenticity meet. That is why this conversation keeps growing. #faith #churchculture #genz",
        ],
    },
    {
        "username": "heraldworlddesk",
        "article": {
            "title": "World Evangelism Conversations Rise as Digital Outreach Expands",
            "content": (
                "Faith leaders and media teams say digital outreach is making world evangelism more visible, measurable, and collaborative. "
                "Short-form content, prayer campaigns, and digital literature distribution are all contributing to the shift."
            ),
            "category": "world evangelism digital outreach missions",
            "image_url": "https://images.unsplash.com/photo-1509099836639-18ba1795216d?w=800",
            "source_url": "https://heraldsocial.app/news/world-evangelism-digital-outreach",
            "likes_count": 204,
        },
        "posts": [
            "World evangelism is not a side conversation anymore. Digital outreach is turning it into a daily measurable movement. #worldevangelism #missions #digitaloutreach",
            "When media, prayer, and discipleship align, the reach of the gospel expands faster and farther. #evangelism #gospel #missions",
        ],
    },
    {
        "username": "heraldworship",
        "article": {
            "title": "Live Worship Night Announced for Herald Social Community",
            "content": (
                "Herald Social has announced a live worship night focused on prayer, songs of faith, and community participation. "
                "The event is expected to bring worship leaders, creators, and everyday users into one shared moment."
            ),
            "category": "worship live event herald social",
            "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
            "source_url": "https://heraldsocial.app/news/live-worship-night",
            "likes_count": 149,
        },
        "posts": [
            "There is something powerful about live worship moments that gather a whole community around one focus. #worship #live #community",
            "People do not just want content. They want encounter, participation, and shared moments of worship. #heraldsocial #worship #faith",
        ],
    },
]


class Command(BaseCommand):
    help = "Seed official Herald users, posts, and news articles for the clustered news experience"

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete previously seeded official Herald content first")
        parser.add_argument("--skip-posts", action="store_true", help="Skip creating feed posts")
        parser.add_argument("--skip-news", action="store_true", help="Skip creating news articles")

    def handle(self, *args, **options):
        rng = random.Random(42)

        if options["clear"]:
            self._clear_seeded_data()

        profiles = self._create_users()
        created_posts = 0 if options["skip_posts"] else self._create_posts(profiles, rng)
        created_news = 0 if options["skip_news"] else self._create_news(rng)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete: {len(profiles)} official users ready, {created_posts} posts created, {created_news} news articles created."
            )
        )

    def _create_users(self):
        profiles = {}

        for spec in OFFICIAL_USERS:
            username = spec["username"]
            email = f"{username}@heraldsocial.app"

            auth_user, auth_created = AuthUser.objects.get_or_create(
                username=username,
                defaults={
                    "email": email,
                    "is_active": True,
                },
            )
            if auth_created:
                auth_user.set_unusable_password()
                auth_user.save(update_fields=["password"])

            profile, created = UserProfile.objects.get_or_create(
                user_id=auth_user,
                defaults={
                    "username": username,
                    "display_name": spec["display_name"],
                    "email": email,
                    "bio": spec["bio"],
                    "tier": spec["tier"],
                    "is_verified": spec["is_verified"],
                    "is_creator": True,
                    "onboarding_completed": True,
                    "auth_provider": "password",
                },
            )

            updates = []
            if profile.username != username:
                profile.username = username
                updates.append("username")
            if profile.display_name != spec["display_name"]:
                profile.display_name = spec["display_name"]
                updates.append("display_name")
            if profile.email != email:
                profile.email = email
                updates.append("email")
            if profile.bio != spec["bio"]:
                profile.bio = spec["bio"]
                updates.append("bio")
            if profile.tier != spec["tier"]:
                profile.tier = spec["tier"]
                updates.append("tier")
            if profile.is_verified != spec["is_verified"]:
                profile.is_verified = spec["is_verified"]
                updates.append("is_verified")
            if not profile.is_creator:
                profile.is_creator = True
                updates.append("is_creator")
            if not profile.onboarding_completed:
                profile.onboarding_completed = True
                updates.append("onboarding_completed")

            if updates:
                profile.save(update_fields=updates)

            profiles[username] = profile
            action = "Created" if created else "Reused"
            self.stdout.write(f"  {action} official user: {username}")

        return profiles

    def _create_posts(self, profiles, rng):
        created_count = 0
        now = timezone.now()

        for packet_index, packet in enumerate(STORY_PACKETS):
            profile = profiles[packet["username"]]
            for post_index, content in enumerate(packet["posts"]):
                if Post.objects.filter(author_id=profile, content=content).exists():
                    continue

                created_at = now - timedelta(hours=(packet_index * 9) + (post_index * 3) + rng.randint(1, 4))
                post = Post.objects.create(
                    author_id=profile,
                    content=content,
                    likes_count=20 + (packet_index * 7) + post_index,
                    comments_count=4 + (packet_index % 5) + post_index,
                    shares_count=3 + (packet_index % 4),
                    bookmarks_count=2 + (packet_index % 3),
                    httn_earned=15 + packet_index,
                )
                Post.objects.filter(pk=post.pk).update(created_at=created_at, updated_at=created_at)
                created_count += 1

        self.stdout.write(f"  Created {created_count} official Herald posts")
        return created_count

    def _create_news(self, rng):
        created_count = 0
        now = timezone.now()

        for packet_index, packet in enumerate(STORY_PACKETS):
            article_spec = packet["article"]
            if NewsArticle.objects.filter(title=article_spec["title"]).exists():
                continue

            created_at = now - timedelta(hours=(packet_index * 7) + rng.randint(1, 6))
            article = NewsArticle.objects.create(
                title=article_spec["title"],
                source=article_source(article_spec["category"]),
                content=article_spec["content"],
                category=article_spec["category"],
                source_url=article_spec["source_url"],
                image_url=article_spec["image_url"],
                likes_count=article_spec["likes_count"],
            )
            NewsArticle.objects.filter(pk=article.pk).update(created_at=created_at)
            created_count += 1

        self.stdout.write(f"  Created {created_count} official Herald news articles")
        return created_count

    def _clear_seeded_data(self):
        usernames = [spec["username"] for spec in OFFICIAL_USERS]
        titles = [packet["article"]["title"] for packet in STORY_PACKETS]

        deleted_posts = Post.objects.filter(author_id__username__in=usernames).delete()[0]
        deleted_news = NewsArticle.objects.filter(title__in=titles).delete()[0]
        deleted_profiles = UserProfile.objects.filter(username__in=usernames).delete()[0]
        deleted_auth = AuthUser.objects.filter(username__in=usernames).delete()[0]

        self.stdout.write(
            f"  Cleared {deleted_posts} posts, {deleted_news} news articles, {deleted_profiles} profiles, {deleted_auth} auth users"
        )
