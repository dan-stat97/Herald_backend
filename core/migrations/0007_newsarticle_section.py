from django.db import migrations, models


SPORTS_KEYWORDS = (
    'sport', 'sports', 'football', 'soccer', 'basketball', 'nba', 'nfl', 'fifa', 'uefa',
    'premier', 'league', 'match', 'goal', 'tennis', 'cricket', 'boxing', 'ufc', 'olympic',
    'athletics', 'formula', 'motorsport', 'champions', 'laliga',
)
ENTERTAINMENT_KEYWORDS = (
    'entertainment', 'movie', 'movies', 'film', 'music', 'album', 'artist', 'celebrity',
    'show', 'tv', 'series', 'netflix', 'hollywood', 'award', 'festival', 'concert',
    'cinema', 'streaming', 'actor', 'actress', 'comedy',
)


def classify_section(article):
    category = (getattr(article, 'category', '') or '').strip().lower().replace('-', '_')
    if category in {'sport', 'sports'}:
        return 'sports'
    if category in {'entertainment', 'music', 'movies', 'movie', 'film', 'tv'}:
        return 'entertainment'

    haystack = ' '.join(
        filter(
            None,
            [
                getattr(article, 'title', '') or '',
                getattr(article, 'content', '') or '',
                getattr(article, 'category', '') or '',
                getattr(article, 'source', '') or '',
                getattr(article, 'source_type', '') or '',
            ],
        )
    ).lower()

    if any(keyword in haystack for keyword in SPORTS_KEYWORDS):
        return 'sports'
    if any(keyword in haystack for keyword in ENTERTAINMENT_KEYWORDS):
        return 'entertainment'
    return 'news'


def backfill_sections(apps, schema_editor):
    NewsArticle = apps.get_model('core', 'NewsArticle')
    for article in NewsArticle.objects.all().only('id', 'title', 'content', 'category', 'source', 'source_type'):
        section = classify_section(article)
        NewsArticle.objects.filter(pk=article.pk).update(section=section)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_newsarticle_views_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsarticle',
            name='section',
            field=models.CharField(db_index=True, default='news', max_length=20),
        ),
        migrations.RunPython(backfill_sections, noop_reverse),
    ]
