from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_callsession_devicepushtoken'),
        ('adminpanel', '0004_adcampaign_display_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminRoleAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('super_admin', 'Super Admin'), ('admin', 'Admin'), ('moderator', 'Moderator'), ('support', 'Support'), ('analytics_viewer', 'Analytics Viewer'), ('ads_manager', 'Ads Manager')], max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='admin_roles_created', to='users.user')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_role_assignment', to='users.user')),
            ],
            options={
                'db_table': 'admin_role_assignments',
                'ordering': ['role', 'created_at'],
            },
        ),
    ]
