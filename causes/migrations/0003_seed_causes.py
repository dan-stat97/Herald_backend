"""
Migration 0003 - seed demo causes and donations.

RunPython is never faked by migrate_safe, so this runs exactly once on production.
"""
import uuid
import random
from datetime import timedelta, date

from django.db import migrations
from django.utils import timezone


SEED_CAUSES = [
    {
        "title": "Healing School Scholarship Fund 2025",
        "description": "Help send 50 young people from low-income families to the Healing School in Johannesburg this year. The Healing School has changed thousands of lives through supernatural encounters and the Word of God. Your donation covers flights, accommodation, and programme fees for selected candidates.",
        "category": "healing_school",
        "goal_amount": "5000000.00",
        "raised_amount": "3120000.00",
        "image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800",
        "status": "active",
        "days_from_now": 45,
        "creator_username": "grace_ikenna",
    },
    {
        "title": "Build a Library for St. Matthew's Primary School, Owerri",
        "description": "St. Matthew's Primary School in Owerri currently has over 800 pupils but no dedicated library. We are raising funds to construct and stock a proper library with over 2,000 books, reading tables, shelves, and digital learning tablets. Education is the greatest investment we can make in a child's future.",
        "category": "education",
        "goal_amount": "2500000.00",
        "raised_amount": "890000.00",
        "image_url": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800",
        "status": "active",
        "days_from_now": 60,
        "creator_username": "esther_nwosu",
    },
    {
        "title": "Daystar Church Audio-Visual Upgrade",
        "description": "Our congregation has grown tremendously but our sound and projection equipment is over 10 years old and failing regularly during services. We need to upgrade to a full digital mixing board, new speakers, LED walls, and lighting rigs. This will serve not just our church but the wider community we host for events.",
        "category": "church",
        "goal_amount": "8000000.00",
        "raised_amount": "4750000.00",
        "image_url": "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?w=800",
        "status": "active",
        "days_from_now": 30,
        "creator_username": "pastor_samuel",
    },
    {
        "title": "Feed 1,000 Families in Jos This Christmas",
        "description": "Last Christmas we reached 400 families in crisis in Plateau State. This year we are believing God for 1,000 families. Each food parcel contains rice, beans, garri, palm oil, tomato paste, and seasoning sufficient for a family of six for two weeks. Join us to put smiles on faces this festive season.",
        "category": "outreach",
        "goal_amount": "3000000.00",
        "raised_amount": "1200000.00",
        "image_url": "https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=800",
        "status": "active",
        "days_from_now": 90,
        "creator_username": "ngozi_inspire",
    },
    {
        "title": "Print 10,000 Gospel Tracts for Campus Outreach",
        "description": "Our campus fellowship is planning a massive outreach across 5 universities in Lagos and Ogun State in the coming semester. We need funds to print high-quality gospel tracts, evangelism booklets, and the Gospel of John in large quantities. Every tract is a seed that can yield an eternal harvest.",
        "category": "scripture",
        "goal_amount": "500000.00",
        "raised_amount": "320000.00",
        "image_url": "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800",
        "status": "active",
        "days_from_now": 21,
        "creator_username": "brother_felix",
    },
    {
        "title": "Sponsor a Child's Education in Kaduna State",
        "description": "Over 3 million children are out of school in northern Nigeria. For just N30,000 per term you can sponsor a child's full primary school education including fees, uniforms, books, and meals. We currently have 47 children on the waiting list. Every child deserves to learn.",
        "category": "education",
        "goal_amount": "4200000.00",
        "raised_amount": "1960000.00",
        "image_url": "https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=800",
        "status": "active",
        "days_from_now": 120,
        "creator_username": "adaeze_health",
    },
    {
        "title": "Mobile Medical Mission to Delta State Villages",
        "description": "Many villages in Delta State have never seen a doctor. Our team of 12 volunteer medical professionals plans a 5-day mobile medical mission providing free consultations, malaria treatment, diabetes and hypertension screening, deworming for children, and basic surgery. We need to fund transport, drugs, and equipment.",
        "category": "outreach",
        "goal_amount": "1800000.00",
        "raised_amount": "1800000.00",
        "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=800",
        "status": "completed",
        "days_from_now": None,
        "creator_username": "adaeze_health",
    },
    {
        "title": "New Church Building for Redeemed Assembly, Maiduguri",
        "description": "Our congregation in Maiduguri has been meeting under a tent for 3 years after our building was destroyed. By God's grace we have survived and grown to 300 members. We need to build a permanent structure that can seat 500, with classrooms for the children's ministry and a pastor's office.",
        "category": "church",
        "goal_amount": "12000000.00",
        "raised_amount": "3400000.00",
        "image_url": "https://images.unsplash.com/photo-1520637836862-4d197d17c93a?w=800",
        "status": "active",
        "days_from_now": 180,
        "creator_username": "pastor_samuel",
    },
    {
        "title": "Distribute Bibles to 500 New Believers in Zamfara",
        "description": "God is moving powerfully in Zamfara State and hundreds of new believers have come to faith in recent months. Many do not own a Bible. We are raising funds to purchase and distribute 500 Hausa-language Bibles to these new members of the body of Christ. The Word is their foundation.",
        "category": "scripture",
        "goal_amount": "750000.00",
        "raised_amount": "750000.00",
        "image_url": "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=800",
        "status": "completed",
        "days_from_now": None,
        "creator_username": "kingsley_vision",
    },
    {
        "title": "Healing School Partner — Send a Widow to Johannesburg",
        "description": "Sister Patience lost her husband last year and has been bedridden with an undetermined illness for 8 months. The doctors have done what they can. We believe God for her complete healing and are raising funds to send her and a companion to the Healing School in Johannesburg as Healing School partners.",
        "category": "healing_school",
        "goal_amount": "650000.00",
        "raised_amount": "427000.00",
        "image_url": "https://images.unsplash.com/photo-1529070538774-1843cb3265df?w=800",
        "status": "active",
        "days_from_now": 14,
        "creator_username": "chioma_faith",
    },
    {
        "title": "Youth Skills Empowerment Workshop Series",
        "description": "We are running a 12-week skills empowerment programme for unemployed youth aged 18-30 in Surulere, Lagos. Skills include graphic design, social media management, copywriting, tailoring, and catering. Funds cover facilitator fees, materials, laptops for the digital tracks, and certificates. 40 slots available.",
        "category": "education",
        "goal_amount": "2200000.00",
        "raised_amount": "980000.00",
        "image_url": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?w=800",
        "status": "active",
        "days_from_now": 55,
        "creator_username": "ngozi_inspire",
    },
    {
        "title": "Street Evangelism Mega Drive — Ibadan",
        "description": "Our church is planning a city-wide street evangelism blitz across all 11 local government areas of Ibadan, Nigeria's second largest city. We need vans, PA systems, gospel materials, and food for our team of 200 volunteers over a 3-day period. Our target: 50,000 gospel presentations in 72 hours.",
        "category": "outreach",
        "goal_amount": "1500000.00",
        "raised_amount": "630000.00",
        "image_url": "https://images.unsplash.com/photo-1491841550275-ad7854e35ca6?w=800",
        "status": "active",
        "days_from_now": 35,
        "creator_username": "brother_felix",
    },
]

SEED_DONATIONS = [
    # (cause_index, donor_username, amount, message, is_anonymous)
    (0, "david_okafor",    "50000.00",  "Believing God for every young person who goes!", False),
    (0, "kingsley_vision", "100000.00", "May God multiply this investment.", False),
    (0, "adaeze_health",   "25000.00",  None, True),
    (1, "emeka_tech",      "20000.00",  "Education changes everything. Happy to contribute.", False),
    (1, "mercy_abara",     "5000.00",   "Every little helps!", False),
    (2, "tobenna_creates", "150000.00", "Sound quality matters for the message to land.", False),
    (2, "grace_ikenna",    "75000.00",  None, False),
    (3, "chioma_faith",    "30000.00",  "Praying this blesses many families.", False),
    (3, "esther_nwosu",    "15000.00",  None, True),
    (4, "mercy_abara",     "10000.00",  "Let the Word go forth!", False),
    (5, "emeka_tech",      "30000.00",  "Education is the greatest investment.", False),
    (6, "kingsley_vision", "200000.00", "Honoured to support this medical mission.", False),
    (6, "david_okafor",    "100000.00", None, False),
    (9, "grace_ikenna",    "50000.00",  "Believing God for Sister Patience's total healing.", False),
    (10, "tobenna_creates", "40000.00", "Skills = dignity. Well done!", False),
    (11, "pastor_samuel",  "80000.00",  "May God save thousands in Ibadan!", False),
]


def seed_forward(apps, schema_editor):
    import traceback as tb

    if schema_editor.connection.vendor != 'postgresql':
        return

    UserProfile = apps.get_model('users', 'User')
    Cause = apps.get_model('causes', 'Cause')
    Donation = apps.get_model('causes', 'Donation')

    now = timezone.now()
    rng = random.Random(99)

    # Build a lookup of seeded users
    creator_map = {}
    for username in set(c["creator_username"] for c in SEED_CAUSES):
        try:
            creator_map[username] = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            pass

    if not creator_map:
        # Fall back to any existing user
        first_user = UserProfile.objects.first()
        if not first_user:
            print("[0003_causes] No users found — skipping cause seed.")
            return
        for c in SEED_CAUSES:
            creator_map[c["creator_username"]] = first_user

    causes_created = 0
    cause_objects = {}

    for i, c in enumerate(SEED_CAUSES):
        if Cause.objects.filter(title=c["title"]).exists():
            cause_objects[i] = Cause.objects.get(title=c["title"])
            continue
        creator = creator_map.get(c["creator_username"])
        if not creator:
            continue
        try:
            hours_ago = rng.randint(24, 30 * 24)
            end_date = None
            if c["days_from_now"] is not None:
                end_date = (now + timedelta(days=c["days_from_now"])).date()

            cause = Cause.objects.create(
                id=uuid.uuid4(),
                title=c["title"],
                description=c["description"],
                category=c["category"],
                created_by=creator,
                goal_amount=c["goal_amount"],
                raised_amount=c["raised_amount"],
                image_url=c.get("image_url"),
                status=c["status"],
                end_date=end_date,
            )
            cause_objects[i] = cause
            causes_created += 1
        except Exception:
            print(f"[0003_causes] Failed to create cause: {c['title'][:60]}")
            tb.print_exc()

    print(f"[0003_causes] Created {causes_created} causes.")

    donations_created = 0
    for cause_idx, donor_username, amount, message, is_anonymous in SEED_DONATIONS:
        cause = cause_objects.get(cause_idx)
        if not cause:
            continue
        donor = creator_map.get(donor_username)
        if not donor:
            try:
                donor = UserProfile.objects.get(username=donor_username)
            except UserProfile.DoesNotExist:
                continue
        try:
            if Donation.objects.filter(cause=cause, donor=donor, amount=amount).exists():
                continue
            Donation.objects.create(
                id=uuid.uuid4(),
                cause=cause,
                donor=donor,
                amount=amount,
                message=message,
                is_anonymous=is_anonymous,
            )
            donations_created += 1
        except Exception:
            print(f"[0003_causes] Failed to create donation for {donor_username}")
            tb.print_exc()

    print(f"[0003_causes] Created {donations_created} donations.")


def seed_backwards(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    Cause = apps.get_model('causes', 'Cause')
    titles = [c["title"] for c in SEED_CAUSES]
    Cause.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('causes', '0002_add_donation_model'),
        # Ensure seeded users exist before we reference them
        ('core', '0004_seed_news_and_users'),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_backwards),
    ]
