"""
Migration 0002 - seed demo store products.

RunPython is never faked by migrate_safe, so this runs exactly once on production.
"""
import uuid

from django.db import migrations
from django.utils import timezone


SEED_PRODUCTS = [
    # ── NFTs ─────────────────────────────────────────────────────────────────
    {
        "name": "Herald Genesis NFT #001",
        "description": "The first edition Herald Social Genesis NFT. Ownership grants lifetime Premium access, an exclusive profile badge, and early access to all future Herald features. Only 100 minted.",
        "category": "nfts",
        "price": "25000.00",
        "image_url": "https://images.unsplash.com/photo-1620321023374-d1a68fbc720d?w=800",
    },
    {
        "name": "Faith Warriors NFT Collection",
        "description": "A limited collection of 500 unique digital artworks celebrating African Christian identity. Each NFT comes with exclusive Discord access and monthly Kingdom Investor calls with the Herald team.",
        "category": "nfts",
        "price": "15000.00",
        "image_url": "https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=800",
    },
    {
        "name": "The Overcomer Badge NFT",
        "description": "A commemorative NFT awarded to those who completed the 30-Day Herald Prayer Challenge. Displays as a special animated badge on your Herald profile. Limited to challenge participants.",
        "category": "nfts",
        "price": "5000.00",
        "image_url": "https://images.unsplash.com/photo-1559136555-9303baea8ebd?w=800",
    },
    {
        "name": "Gospel Artisan NFT — Series 1",
        "description": "Hand-crafted digital art by Nigerian Christian artists minted on-chain. 12 unique pieces in this series celebrating the spread of the Gospel across Africa. Collect all 12.",
        "category": "nfts",
        "price": "8500.00",
        "image_url": "https://images.unsplash.com/photo-1549490349-8643362247b5?w=800",
    },

    # ── Tools ─────────────────────────────────────────────────────────────────
    {
        "name": "Herald Content Creator Toolkit",
        "description": "Everything you need to grow your Herald following. Includes a 90-day content calendar, 500 faith-based caption templates, hashtag research guide, posting time optimizer, and a video script framework for Herald Reels.",
        "category": "tools",
        "price": "12000.00",
        "image_url": "https://images.unsplash.com/photo-1611532736597-de2d4265fba3?w=800",
    },
    {
        "name": "Kingdom Business Blueprint",
        "description": "A comprehensive digital workbook for faith-driven entrepreneurs. Covers vision alignment, business planning, pricing, marketing, and integrating your faith values into every business decision. 120-page PDF + 6 video modules.",
        "category": "tools",
        "price": "18000.00",
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800",
    },
    {
        "name": "Prayer Journal Digital Template Pack",
        "description": "30 beautifully designed digital prayer journal templates compatible with Notability, GoodNotes, and PDF. Includes gratitude pages, scripture meditation pages, prayer request trackers, and monthly reflection spreads.",
        "category": "tools",
        "price": "4500.00",
        "image_url": "https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=800",
    },
    {
        "name": "Social Media Evangelism Masterclass",
        "description": "Learn how to use Instagram, TikTok, and Herald Social to share the Gospel effectively. 8 modules covering storytelling, objection handling in comments, going viral with faith content, and building an online ministry from scratch.",
        "category": "tools",
        "price": "22000.00",
        "image_url": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800",
    },
    {
        "name": "Herald Analytics Pro Dashboard",
        "description": "Unlock deep analytics for your Herald creator account. Track follower growth, post reach, engagement rates, donation trends for your causes, and audience demographics. Export data to CSV. 30-day rolling insights.",
        "category": "tools",
        "price": "9000.00",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800",
    },

    # ── Subscriptions ─────────────────────────────────────────────────────────
    {
        "name": "Herald Premium — Monthly",
        "description": "Upgrade to Herald Premium and unlock exclusive features: verified badge eligibility, unlimited post scheduling, priority customer support, ad-free browsing, early access to beta features, and 2x HTTN token earning rate.",
        "category": "subscriptions",
        "price": "2500.00",
        "image_url": "https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=800",
    },
    {
        "name": "Herald Premium — Annual (Save 30%)",
        "description": "Everything in Herald Premium Monthly at a 30% discount. One upfront payment for 12 months of premium access. Includes a bonus Welcome Pack with exclusive digital wallpapers and a 500 HTTN token bonus on activation.",
        "category": "subscriptions",
        "price": "21000.00",
        "image_url": "https://images.unsplash.com/photo-1553729459-efe14ef6055d?w=800",
    },
    {
        "name": "Herald Creator Pro — Monthly",
        "description": "The ultimate plan for serious creators and ministries. Includes everything in Premium plus a custom profile theme, featured placement in the Creator Directory, monthly 1-on-1 growth coaching session, and priority cause promotion.",
        "category": "subscriptions",
        "price": "7500.00",
        "image_url": "https://images.unsplash.com/photo-1512314889357-e157c22f938d?w=800",
    },
    {
        "name": "Herald Church Plan — Monthly",
        "description": "Built for churches and ministries. Manage up to 10 team accounts under one subscription, broadcast announcements to all followers, live stream Sunday services directly on Herald, and access detailed congregation analytics.",
        "category": "subscriptions",
        "price": "15000.00",
        "image_url": "https://images.unsplash.com/photo-1548438294-1ad5d5f4f063?w=800",
    },

    # ── Merchandise ───────────────────────────────────────────────────────────
    {
        "name": "Herald Social Classic Tee",
        "description": "Premium 100% cotton Herald Social branded t-shirt. Features the Herald logo on the chest and 'Faith. Community. Impact.' on the back. Available in black, white, and navy. Unisex sizing S–3XL.",
        "category": "merchandise",
        "price": "6500.00",
        "image_url": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800",
    },
    {
        "name": "Herald Faith Hoodie",
        "description": "Stay warm and represent the kingdom. Heavyweight fleece hoodie with embroidered Herald logo on the left chest and a large back print featuring Psalm 119:105. Available in charcoal, cream, and forest green. Unisex.",
        "category": "merchandise",
        "price": "14000.00",
        "image_url": "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=800",
    },
    {
        "name": '"His Word is a Lamp" Study Bible Cover',
        "description": "Handcrafted genuine leather Bible cover with the Herald Social logo embossed. Fits standard A5 study Bibles. Includes a built-in bookmark ribbon, pen holder, and card slots. Available in brown and black.",
        "category": "merchandise",
        "price": "8500.00",
        "image_url": "https://images.unsplash.com/photo-1504052434569-70ad5836ab65?w=800",
    },
    {
        "name": "Herald Enamel Mug — 'Morning by Morning'",
        "description": "Start your devotions right. Premium 350ml enamel mug printed with Lamentations 3:23 and the Herald Social wordmark. Dishwasher safe. Makes a great gift for believers who love their morning quiet time.",
        "category": "merchandise",
        "price": "4000.00",
        "image_url": "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=800",
    },
    {
        "name": "Herald Tote Bag — Carry the Word",
        "description": "Heavy-duty canvas tote bag with reinforced handles. Printed with 'Carry the Word' and Isaiah 52:7 on one side and the Herald Social logo on the other. Available in natural and black. Great for church, market, or campus.",
        "category": "merchandise",
        "price": "3500.00",
        "image_url": "https://images.unsplash.com/photo-1590739293931-a8cca0d2cd4f?w=800",
    },
    {
        "name": "Herald Wristband 3-Pack",
        "description": "Set of three silicone wristbands with faith affirmations: 'I Am More Than A Conqueror', 'His Grace is Sufficient', and the Herald Social logo band. Share with friends or wear as a daily reminder of your identity in Christ.",
        "category": "merchandise",
        "price": "2000.00",
        "image_url": "https://images.unsplash.com/photo-1573408301185-9519f94cbf1d?w=800",
    },
    {
        "name": "Devotional Planner 2025 — Kingdom Edition",
        "description": "A beautifully printed 12-month physical planner that integrates daily scripture, a 52-week Bible reading plan, monthly goal-setting pages, prayer logs, and space for journaling. A5 hardcover with ribbon bookmark. Ships within Nigeria.",
        "category": "merchandise",
        "price": "7000.00",
        "image_url": "https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=800",
    },
]


def seed_forward(apps, schema_editor):
    import traceback as tb

    if schema_editor.connection.vendor != 'postgresql':
        return

    Product = apps.get_model('estore', 'Product')

    created = 0
    for p in SEED_PRODUCTS:
        if Product.objects.filter(name=p["name"]).exists():
            continue
        try:
            Product.objects.create(
                id=uuid.uuid4(),
                name=p["name"],
                description=p["description"],
                category=p["category"],
                price=p["price"],
                image_url=p.get("image_url"),
            )
            created += 1
        except Exception:
            print(f"[0002_products] Failed to create product: {p['name'][:60]}")
            tb.print_exc()

    print(f"[0002_products] Created {created} products.")


def seed_backwards(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    Product = apps.get_model('estore', 'Product')
    names = [p["name"] for p in SEED_PRODUCTS]
    Product.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_forward, seed_backwards),
    ]
