# Generated by Django 5.0.4 on 2024-10-01 17:21

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_profile_customer_profile_subscription'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileStateTransition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('from_state', models.CharField(choices=[('stranger', 'Stranger'), ('signed_up', 'Signed Up'), ('subscribed', 'Subscribed'), ('cancelled', 'Cancelled'), ('account_deleted', 'Account Deleted')], max_length=255)),
                ('to_state', models.CharField(choices=[('stranger', 'Stranger'), ('signed_up', 'Signed Up'), ('subscribed', 'Subscribed'), ('cancelled', 'Cancelled'), ('account_deleted', 'Account Deleted')], max_length=255)),
                ('backup_profile_id', models.IntegerField()),
                ('metadata', models.JSONField(blank=True, null=True)),
                ('profile', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='state_transitions', to='core.profile')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
