from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0002_seed_products'),
        ('users', '0006_user_location_user_website'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='seller',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='listed_products',
                to='users.user',
            ),
        ),
    ]
