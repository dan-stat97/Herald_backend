from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estore', '0003_product_seller'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(db_index=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
    ]
