"""
Management command: seed_data
Creates seed users, posts, and news articles for development/demo purposes.

Usage:
    python manage.py seed_data
    python manage.py seed_data --users 20 --posts-per-user 15 --news 40
    python manage.py seed_data --clear   (deletes all seeded data first)
"""

import random
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User as UserProfile
from posts.models import Post
from core.models import NewsArticle

AuthUser = get_user_model()

# ── Seed content ──────────────────────────────────────────────────────────────

SEED_USERS = [
    {
        "username": "grace_ikenna",
        "display_name": "Grace Ikenna",
        "bio": "Faith. Hope. Love. Living boldly for Christ. 🙏",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "david_okafor",
        "display_name": "David Okafor",
        "bio": "Tech entrepreneur | Building the future one line at a time 💡",
        "tier": "premium",
        "is_verified": True,
    },
    {
        "username": "esther_nwosu",
        "display_name": "Esther Nwosu",
        "bio": "Children's educator & author. Raising world-changers 🌟",
        "tier": "creator",
        "is_verified": False,
    },
    {
        "username": "pastor_samuel",
        "display_name": "Pastor Samuel Adeyemi",
        "bio": "Senior Pastor, Daystar Christian Centre. Author. Speaker.",
        "tier": "premium",
        "is_verified": True,
    },
    {
        "username": "chioma_faith",
        "display_name": "Chioma Faith",
        "bio": "Worship leader | Musician | Lover of God ✨",
        "tier": "creator",
        "is_verified": False,
    },
    {
        "username": "emeka_tech",
        "display_name": "Emeka Eze",
        "bio": "Software engineer. Open source. Coffee ☕ and code.",
        "tier": "free",
        "is_verified": False,
    },
    {
        "username": "ngozi_inspire",
        "display_name": "Ngozi Obi",
        "bio": "Life coach | Helping women walk in their purpose 💪",
        "tier": "creator",
        "is_verified": True,
    },
    {
        "username": "brother_felix",
        "display_name": "Felix Okonkwo",
        "bio": "Youth minister | Footballer | God's guy 🙌",
        "tier": "free",
        "is_verified": False,
    },
    {
        "username": "adaeze_health",
        "display_name": "Dr. Adaeze Oti",
        "bio": "Medical doctor | Health & wellness advocate | Mother of 3",
        "tier": "premium",
        "is_verified": True,
    },
    {
        "username": "tobenna_creates",
        "display_name": "Tobenna Ani",
        "bio": "Creative director | Brand designer | Making beautiful things ✏️",
        "tier": "creator",
        "is_verified": False,
    },
    {
        "username": "mercy_abara",
        "display_name": "Mercy Abara",
        "bio": "Student. Bookworm. Future lawyer. Faith is my foundation.",
        "tier": "free",
        "is_verified": False,
    },
    {
        "username": "kingsley_vision",
        "display_name": "Kingsley Amos",
        "bio": "Business coach | Investor | Raising kingdom builders 🔥",
        "tier": "premium",
        "is_verified": True,
    },
]

POST_TEMPLATES = [
    # Faith
    "God's grace is sufficient for every situation you face today. Don't give up — He's working it out. 🙏",
    "Started my morning in prayer and the peace that followed me all day was unreal. Try it tomorrow!",
    "The Word says 'I can do all things through Christ who strengthens me.' That promise is for YOU today.",
    "Grateful for another day of life. Every breath is a gift from God. Don't take it for granted. 🙌",
    "Faith without works is dead. What action are you taking today to match what you believe for?",
    "Sunday service recap: God showed up in a powerful way today. The presence was tangible. 🔥",
    "Reminder: Your breakthrough is closer than it appears. Hold on. Don't let go of God's promises.",
    "I prayed about that situation for 3 months. Today I got the answer. God is never late. 🕊️",
    "The Bible says worry about nothing, pray about everything. Philippians 4:6 — live by it.",
    "Fasting and prayer changes things. Not because of our strength but because of His faithfulness.",
    # Inspiration / Life
    "Stop waiting for the perfect moment. The perfect moment is NOW. Start that thing you've been putting off.",
    "Your network is your net worth. Surround yourself with people who challenge you to grow. 💡",
    "Failure is not final. Every great success story has chapters of failure in it. Keep writing yours.",
    "Self-discipline is the bridge between goals and accomplishment. Build it daily.",
    "You don't need more motivation. You need more consistency. Show up even when you don't feel like it.",
    "Comparison is the thief of joy. Run your race, not someone else's.",
    "Success is not accidental. It's the result of daily intentional choices. Choose wisely today.",
    "The people who succeed aren't smarter than you — they just didn't quit when it got hard.",
    "Invest in yourself first. Your mind, your health, your skills. Everything else flows from there.",
    "Dream big, plan smart, execute daily. That's the formula.",
    # Community / Social
    "Lagos traffic is a whole spiritual exercise in patience 😂 But you know what? I arrived and still on time.",
    "This community is something else! The conversations here are genuinely life-changing. 💙",
    "Just finished a 5km run this morning! Starting the week right. Who else is on a fitness journey?",
    "Homemade jollof rice > restaurant jollof rice. Fight me. 😂🍚",
    "Took my kids to church today. Their questions during the sermon had me cracking up the whole way home.",
    "Anyone else in Lagos using Herald Social? Let's connect! The community here is amazing.",
    "Just completed a 30-day Bible reading plan. Feeling spiritually refreshed. Highly recommend!",
    "The power went out for 6 hours and I finished an entire book. Maybe NEPA is teaching me something 😂📚",
    "Accountability partners change everything. Find someone who will check on your goals — not just your vibes.",
    "Weather in Abuja has been beautiful lately. Perfect for outdoor morning devotions 🌅",
    # Tech / Professional
    "Just shipped a new feature at work. The satisfaction of seeing it go live never gets old. 💻",
    "AI is not going to replace you. A person who knows AI will. Time to learn.",
    "Remote work tip: your morning routine matters MORE when no one is watching you.",
    "3 years ago I had no idea how to code. Today I deployed my first full-stack app. 🚀 Never stop learning.",
    "The best investment in 2025 is still you. Your skills, your mind, your character.",
    # Health
    "Week 4 of cutting out sugar. The energy levels are unreal. My body is thanking me already.",
    "Mental health is health. Take care of your mind the same way you take care of your body.",
    "Drank 3 litres of water today. Skin is glowing. Sleep was deep. Simple things, big results.",
    "Rest is not laziness. High performers know how to recover. Prioritize your sleep.",
    "Been walking 10,000 steps daily for a month. Down 4kg. No gym. Just consistency. 💪",
]

NEWS_ARTICLES = [
    {
        "title": "Church Leaders Across Nigeria Unite for National Prayer Summit",
        "content": (
            "Over 500 church leaders from across Nigeria gathered in Abuja this week for the "
            "National Prayer Summit, an annual event focused on intercession for the nation's "
            "leadership, economy, and security. The summit, now in its 12th year, brought together "
            "pastors from diverse denominations including Pentecostal, Catholic, Anglican, and "
            "Methodist traditions. Key themes this year included peace in the North East, economic "
            "recovery, and raising godly youth. Participants committed to monthly coordinated "
            "prayer sessions until the next summit. Organizers described the turnout as the "
            "largest in the event's history."
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800",
    },
    {
        "title": "Tech Startup Ecosystem in Lagos Records $300M in Funding This Quarter",
        "content": (
            "Lagos continues to cement its position as Africa's premier tech hub after startup "
            "funding in the city surpassed $300 million in a single quarter. Fintech, healthtech, "
            "and edtech sectors led the charge, with several Series A and B rounds closing. "
            "Notable deals include a $45M raise by a payments infrastructure company and a $22M "
            "Series B for a telemedicine platform serving rural communities. Analysts attribute "
            "the growth to improved regulatory clarity from the CBN and a maturing angel investor "
            "ecosystem. The Lagos State government also announced a new digital innovation hub "
            "to be completed by Q3 2026."
        ),
        "category": "technology",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
    },
    {
        "title": "Youth Ministry Conference Draws 20,000 Young People to Eko Hotel Grounds",
        "content": (
            "The annual Shift Youth Conference drew an unprecedented 20,000 young Nigerians "
            "to the Eko Hotel & Suites grounds in Lagos over a three-day period. The conference, "
            "themed 'Unshakeable Generation,' featured speakers from across Africa and beyond, "
            "worship nights, entrepreneurship panels, and mental health workshops. Attendees "
            "ranged from ages 15 to 35. Conference director Pastor Bisi Adewale said the "
            "turnout reflects a genuine hunger among Nigerian youth for both spiritual depth "
            "and practical life skills. Thousands reportedly made first-time commitments of "
            "faith during the altar call on the final night."
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800",
    },
    {
        "title": "Nigeria's Inflation Rate Drops for Third Consecutive Month",
        "content": (
            "Nigeria's headline inflation rate fell for the third consecutive month in March, "
            "dropping to 28.4% from a peak of 33.9% late last year, according to the National "
            "Bureau of Statistics. The decline is attributed to improved food supply chains, "
            "relative naira stability, and the CBN's sustained tight monetary policy stance. "
            "Food inflation, which had been the primary driver, eased from 37.9% to 29.2%. "
            "Economists cautioned that while the trend is encouraging, the rate remains well "
            "above historical averages and households continue to feel pressure at the market. "
            "The government has pointed to ongoing subsidy reform savings as funding source "
            "for targeted food intervention programmes."
        ),
        "category": "economy",
        "image_url": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800",
    },
    {
        "title": "New Gospel Album by Sinach Breaks Streaming Records in Africa",
        "content": (
            "Award-winning gospel artiste Sinach has broken African streaming records with her "
            "latest album 'Overflow,' which surpassed 10 million streams across all platforms "
            "within its first two weeks of release. The album features 12 tracks including the "
            "lead single 'You Are God Alone,' which has already become a worship staple in "
            "churches across Nigeria, Ghana, and Kenya. Sinach, who is globally recognised for "
            "her hit 'Way Maker,' described the album as the most personal she has ever made. "
            "'Every song came out of a real season of my life,' she told reporters. The album "
            "is available on Spotify, Apple Music, and Audiomack."
        ),
        "category": "entertainment",
        "image_url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800",
    },
    {
        "title": "Super Eagles qualify for 2025 AFCON with Dominant Display",
        "content": (
            "Nigeria's Super Eagles secured their qualification for the 2025 Africa Cup of "
            "Nations with a commanding 3-0 victory over Rwanda at the Moshood Abiola Stadium "
            "in Abuja. Goals from Victor Osimhen (brace) and a thunderous strike from Ademola "
            "Lookman sealed the three points in front of a packed 60,000-strong crowd. Head "
            "coach Eric Chelle praised the team's discipline and intensity, calling it one of "
            "their best qualifying performances. Nigeria tops Group C with 15 points from "
            "five games. The Eagles' next fixture is a friendly against Cameroon scheduled "
            "for next month."
        ),
        "category": "sports",
        "image_url": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?w=800",
    },
    {
        "title": "Healthcare Minister Launches Free Maternal Health Initiative in 10 States",
        "content": (
            "Nigeria's Minister of Health has officially launched the Maternal Wellness Initiative, "
            "a federal programme providing free antenatal care, delivery services, and postnatal "
            "support to women in 10 states with the highest maternal mortality rates. The "
            "programme, funded through a combination of federal allocation and World Bank grants, "
            "will operate through 450 primary healthcare centres. Maternal mortality in Nigeria "
            "remains among the highest in the world at approximately 820 deaths per 100,000 "
            "live births. The minister said the goal is to halve that figure within four years. "
            "Civil society organisations welcomed the initiative but called for sustained "
            "budgetary commitment beyond the pilot phase."
        ),
        "category": "health",
        "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800",
    },
    {
        "title": "Dangote Refinery Begins Full Commercial Operations, Petrol Prices Stabilise",
        "content": (
            "The Dangote Petroleum Refinery in Lagos has commenced full commercial operations, "
            "marking a historic moment for Nigeria's energy sector. The 650,000 barrel-per-day "
            "facility, the largest single-train refinery in the world, is now supplying petrol, "
            "diesel, and jet fuel to the domestic market. Industry observers report that pump "
            "prices have stabilised in Lagos and Abuja following the ramp-up. Aliko Dangote, "
            "the refinery's owner, said the plant will save Nigeria approximately $20 billion "
            "annually in foreign exchange previously spent on fuel imports. The refinery is "
            "also expected to create over 100,000 direct and indirect jobs."
        ),
        "category": "economy",
        "image_url": "https://images.unsplash.com/photo-1518186285589-2f7649de83e0?w=800",
    },
    {
        "title": "10 Bible Verses to Strengthen Your Faith in Difficult Times",
        "content": (
            "Life has a way of presenting seasons that challenge even the most seasoned believers. "
            "Whether it's financial pressure, relationship difficulties, or health challenges, "
            "the Word of God remains an anchor for the soul. Here are 10 powerful scriptures "
            "that believers across Africa have leaned on during hard times:\n\n"
            "1. Psalm 46:1 — 'God is our refuge and strength, a very present help in trouble.'\n"
            "2. Isaiah 41:10 — 'Fear not, for I am with you.'\n"
            "3. Romans 8:28 — 'All things work together for good.'\n"
            "4. Philippians 4:13 — 'I can do all things through Christ who strengthens me.'\n"
            "5. Jeremiah 29:11 — 'I know the plans I have for you.'\n"
            "6. Joshua 1:9 — 'Be strong and courageous.'\n"
            "7. Psalm 23:4 — 'Even though I walk through the darkest valley.'\n"
            "8. 2 Corinthians 12:9 — 'My grace is sufficient for you.'\n"
            "9. Nahum 1:7 — 'The Lord is good, a refuge in times of trouble.'\n"
            "10. Matthew 11:28 — 'Come to me, all you who are weary.'"
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800",
    },
    {
        "title": "Nollywood Film 'Rapture' Breaks Box Office Record with ₦500M Opening Weekend",
        "content": (
            "The highly anticipated Nollywood faith-based film 'Rapture' shattered box office "
            "records with a ₦500 million opening weekend, becoming the highest-grossing Nigerian "
            "film in history. Produced by RFG Studios and directed by Niyi Akinmolayan, the "
            "film depicts the end times through the eyes of a Lagos family. The star-studded "
            "cast includes Funke Akindele, Odunlade Adekola, and Mercy Johnson. Churches across "
            "the country organised group viewings, contributing significantly to the numbers. "
            "Film critics have praised its production quality, calling it 'a watershed moment "
            "for African faith cinema.' The film is now showing in cinemas across West Africa "
            "and select UK and US cities with large African diaspora populations."
        ),
        "category": "entertainment",
        "image_url": "https://images.unsplash.com/photo-1478720568477-152d9b164e26?w=800",
    },
    {
        "title": "Cybersecurity Alert: New Phishing Scam Targeting Nigerian Bank Customers",
        "content": (
            "Nigeria's cybersecurity authority has issued a high-priority alert warning bank "
            "customers of a sophisticated new phishing campaign impersonating major commercial "
            "banks. The scam uses fake SMS messages and emails claiming account suspension to "
            "trick victims into clicking malicious links and entering banking credentials. "
            "Reports indicate thousands of customers have already been targeted. The Nigerian "
            "Communications Commission (NCC) has urged the public to never click links in "
            "unsolicited bank messages, to always access internet banking directly through "
            "official websites or verified apps, and to report suspicious activity to their "
            "bank immediately. Banks have been directed to strengthen customer communication "
            "protocols."
        ),
        "category": "technology",
        "image_url": "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=800",
    },
    {
        "title": "Annual Herald Social Prayer Drive Unites Thousands Across Africa",
        "content": (
            "The Herald Social platform's inaugural Prayer Drive event connected over 15,000 "
            "users across Nigeria, Ghana, Kenya, South Africa, and the diaspora in a coordinated "
            "24-hour prayer initiative. Users shared prayer requests, posted testimonies, and "
            "formed virtual prayer groups across the app's community feature. The event trended "
            "nationally on social media with the hashtag #HeraldPrays. Platform founder said "
            "the response exceeded all expectations: 'We built Herald Social for moments like "
            "this — where faith, community, and technology come together for something greater "
            "than any individual.' A second Prayer Drive is already being planned for year-end."
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?w=800",
    },
    {
        "title": "Nigeria Ranks 5th in Africa for Mobile Internet Adoption",
        "content": (
            "A new report by the GSMA has ranked Nigeria 5th in Africa for mobile internet "
            "adoption, with over 85 million active mobile internet users as of Q1 2025. The "
            "report credits falling data costs, increased smartphone affordability, and "
            "widespread 4G coverage as the primary drivers. Lagos and Abuja lead in connectivity "
            "quality while northern states continue to show the widest coverage gaps. The report "
            "also flagged digital literacy as a key challenge to deepening adoption, recommending "
            "government and private sector investment in skills training. Nigeria's tech ecosystem "
            "stands to benefit significantly as more citizens come online."
        ),
        "category": "technology",
        "image_url": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800",
    },
    {
        "title": "Archbishop Announces New Theological Seminary to Open in Port Harcourt",
        "content": (
            "The Anglican Archbishop of the Church of Nigeria has announced the establishment "
            "of a new theological seminary in Port Harcourt, set to open its doors to the "
            "first cohort of students in September 2025. The seminary, named 'Logos Theological "
            "College,' will offer bachelor's and master's degrees in theology, pastoral ministry, "
            "and Christian education. The Archbishop said the institution was necessitated by "
            "the rapid growth of the church and a shortage of formally trained clergy in the "
            "Niger Delta region. The facility will accommodate 300 residential students and "
            "includes a research library, chapel, and digital learning centre. Scholarships "
            "will be available for candidates from underserved communities."
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=800",
    },
    {
        "title": "How Nigeria's Gen Z is Reshaping Church Culture",
        "content": (
            "A growing shift is underway in Nigerian churches as Generation Z begins to "
            "redefine what worship, community, and faith engagement look like. Unlike previous "
            "generations, Gen Z churchgoers are demanding authenticity, intellectual engagement, "
            "and social action from their faith communities. Churches that have adapted — "
            "incorporating contemporary worship, mental health conversations, and social justice "
            "initiatives — are reporting significant youth growth. Sociologists studying religion "
            "in Nigeria say this is the most significant generational shift in church culture "
            "in 30 years. 'They're not abandoning faith,' one researcher noted, 'they're "
            "demanding that faith mean something in the real world.'"
        ),
        "category": "faith",
        "image_url": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800",
    },
    {
        "title": "Nigeria Beats South Africa 2-1 in Basketball AfroBasket Quarterfinals",
        "content": (
            "Team Nigeria's D'Tigers staged a stunning comeback to defeat South Africa 2-1 "
            "in the AfroBasket quarterfinals held in Cairo, Egypt. Trailing by 12 points at "
            "halftime, the D'Tigers rallied behind a blistering third quarter performance led "
            "by point guard Gabe Osabuohien, who finished with 28 points and 9 assists. "
            "The victory sends Nigeria into the semifinals where they will face either Egypt "
            "or Senegal. Nigerian Basketball Federation president expressed pride in the team's "
            "resilience, noting several NBA-level players had returned from overseas to "
            "represent the country. Fans back home flooded social media to celebrate what "
            "many are calling Nigeria's best AfroBasket performance in a decade."
        ),
        "category": "sports",
        "image_url": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=800",
    },
    {
        "title": "Study Reveals Prayer and Mental Health Benefits Among Nigerian Adults",
        "content": (
            "A peer-reviewed study published in the African Journal of Psychology has found "
            "strong correlations between regular prayer practice and improved mental health "
            "outcomes among Nigerian adults. The study, which surveyed 3,400 participants "
            "across six geopolitical zones, found that individuals who prayed daily reported "
            "lower levels of anxiety, stronger social support networks, and greater resilience "
            "under economic stress. Researchers were careful to note that correlation does not "
            "imply causation, but the findings are consistent with similar global studies. "
            "Faith leaders have cited the research as validation for pastoral counselling "
            "programmes. Mental health advocates are calling for more research at the intersection "
            "of spirituality and psychological wellbeing in the African context."
        ),
        "category": "health",
        "image_url": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=800",
    },
    {
        "title": "Free Online Bible College Launched by Leading Nigerian Ministry",
        "content": (
            "One of Nigeria's largest ministries has launched a fully free online Bible college, "
            "offering structured theological education to anyone with internet access. The "
            "programme offers certificates in Biblical Studies, Evangelism, and Church Leadership, "
            "with coursework developed in partnership with three accredited theological institutions. "
            "Over 12,000 students enrolled in the first 48 hours of launch. The ministry's "
            "founder said the vision is to democratise theological education: 'You shouldn't need "
            "money or proximity to a city to receive quality Bible training.' The curriculum is "
            "available in English, Yoruba, Hausa, and Igbo, with plans to add more Nigerian "
            "languages by year end."
        ),
        "category": "education",
        "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800",
    },
    {
        "title": "Lagos Records Highest Number of New Businesses in West Africa",
        "content": (
            "Lagos State has recorded the highest number of newly registered businesses in "
            "West Africa for the second consecutive year, according to data from the Corporate "
            "Affairs Commission. Over 180,000 new businesses were registered in Lagos in 2024, "
            "representing a 22% increase from the previous year. The majority were small and "
            "medium enterprises in retail, food services, and digital services. The Lagos State "
            "Governor attributed the growth to the state's ease-of-doing-business reforms, "
            "reduced registration timelines, and the newly launched MSME credit facility. "
            "Business analysts say the numbers reflect a resilient entrepreneurial culture "
            "even amid macroeconomic headwinds."
        ),
        "category": "economy",
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800",
    },
    {
        "title": "Gospel Artist Nathaniel Bassey to Headline Herald Social's Live Worship Event",
        "content": (
            "Acclaimed trumpeter and gospel artist Nathaniel Bassey has been confirmed as the "
            "headline act for Herald Social's first Live Worship Experience, scheduled for June "
            "in Lagos. The event, titled 'His Presence,' will feature an intimate evening of "
            "worship at a venue to be disclosed to registered attendees. Known for his Hallelujah "
            "Challenge series which has mobilised millions across Africa to pray at midnight, "
            "Nathaniel Bassey said he is excited to partner with Herald Social's mission. "
            "'Technology and worship were always meant to go together,' he said in a statement. "
            "Tickets will be available exclusively to Herald Social premium members first, "
            "with general availability to follow."
        ),
        "category": "entertainment",
        "image_url": "https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=800",
    },
]


class Command(BaseCommand):
    help = "Seed the database with demo users, posts, and news articles"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=len(SEED_USERS),
                            help="Number of users to create (default: all predefined)")
        parser.add_argument("--posts-per-user", type=int, default=8,
                            help="Number of posts to create per user (default: 8)")
        parser.add_argument("--news", type=int, default=len(NEWS_ARTICLES),
                            help="Number of news articles to create (default: all predefined)")
        parser.add_argument("--clear", action="store_true",
                            help="Delete all previously seeded data before seeding")

    def handle(self, *args, **options):
        import traceback
        try:
            if options["clear"]:
                self._clear_seeded_data()

            users_created = self._create_users(options["users"])
            self._create_posts(users_created, options["posts_per_user"])
            self._create_news(options["news"])

            self.stdout.write(self.style.SUCCESS(
                f"\nSeeding complete: {len(users_created)} users, "
                f"{len(users_created) * options['posts_per_user']} posts, "
                f"{min(options['news'], len(NEWS_ARTICLES))} news articles."
            ))
        except Exception as exc:
            self.stderr.write(f"\n[seed_data ERROR] {type(exc).__name__}: {exc}")
            self.stderr.write(traceback.format_exc())
            # Exit 0 so a seed failure never breaks the build
            return

    # ── Users ─────────────────────────────────────────────────────────────────

    def _create_users(self, count):
        created = []
        user_defs = SEED_USERS[:count]

        for u in user_defs:
            username = u["username"]
            email = f"{username}@heraldsocial.demo"

            # Skip if already exists
            if AuthUser.objects.filter(username=username).exists():
                auth_user = AuthUser.objects.get(username=username)
                profile = UserProfile.objects.get(user_id=auth_user)
                self.stdout.write(f"  >>User {username} already exists, skipping create.")
                created.append(profile)
                continue

            # Create Django auth user
            auth_user = AuthUser.objects.create_user(
                username=username,
                email=email,
                password="HeraldDemo2025!",
            )

            # Create user profile
            profile = UserProfile.objects.create(
                user_id=auth_user,
                username=username,
                display_name=u["display_name"],
                email=email,
                bio=u.get("bio", ""),
                tier=u.get("tier", "free"),
                is_verified=u.get("is_verified", False),
                is_creator=u.get("tier") == "creator",
                onboarding_completed=True,
                auth_provider="password",
            )
            created.append(profile)
            self.stdout.write(f"  +Created user: {username}")

        return created

    # ── Posts ─────────────────────────────────────────────────────────────────

    def _create_posts(self, profiles, posts_per_user):
        total = 0
        pool = list(POST_TEMPLATES)

        for profile in profiles:
            # Spread post timestamps over the last 30 days
            templates = random.sample(pool, min(posts_per_user, len(pool)))

            for i, content in enumerate(templates):
                hours_ago = random.randint(1, 30 * 24)
                created_at = timezone.now() - timedelta(hours=hours_ago)

                post = Post(
                    author_id=profile,
                    content=content,
                    likes_count=random.randint(0, 340),
                    comments_count=random.randint(0, 60),
                    shares_count=random.randint(0, 40),
                    bookmarks_count=random.randint(0, 25),
                    httn_earned=random.randint(0, 100),
                )
                post.save()
                # Manually set created_at since auto_now_add prevents it otherwise
                Post.objects.filter(pk=post.pk).update(created_at=created_at)
                total += 1

        self.stdout.write(f"  +Created {total} posts")

    # ── News ──────────────────────────────────────────────────────────────────

    def _create_news(self, count):
        articles = NEWS_ARTICLES[:count]
        created = 0

        for a in articles:
            if NewsArticle.objects.filter(title=a["title"]).exists():
                self.stdout.write(f"  >>News article already exists: {a['title'][:50]}…")
                continue

            hours_ago = random.randint(1, 14 * 24)
            created_at = timezone.now() - timedelta(hours=hours_ago)

            article = NewsArticle(
                title=a["title"],
                content=a["content"],
                category=a["category"],
                image_url=a.get("image_url"),
                source_url=a.get("source_url"),
                likes_count=random.randint(0, 500),
            )
            article.save()
            NewsArticle.objects.filter(pk=article.pk).update(created_at=created_at)
            created += 1

        self.stdout.write(f"  +Created {created} news articles")

    # ── Clear ─────────────────────────────────────────────────────────────────

    def _clear_seeded_data(self):
        usernames = [u["username"] for u in SEED_USERS]
        deleted_posts = Post.objects.filter(
            author_id__username__in=usernames
        ).delete()
        deleted_news = NewsArticle.objects.filter(
            title__in=[a["title"] for a in NEWS_ARTICLES]
        ).delete()
        deleted_profiles = UserProfile.objects.filter(username__in=usernames).delete()
        deleted_auth = AuthUser.objects.filter(username__in=usernames).delete()
        self.stdout.write(
            f"  Cleared: {deleted_posts[0]} posts, {deleted_news[0]} articles, "
            f"{deleted_profiles[0]} profiles, {deleted_auth[0]} auth users"
        )
