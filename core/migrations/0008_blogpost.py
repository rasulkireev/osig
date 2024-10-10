# Generated by Django 5.0.4 on 2024-10-10 07:24

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_image_unique_together_image_image_data_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True)),
                ('slug', models.SlugField(max_length=250)),
                ('tags', models.TextField()),
                ('content', models.TextField()),
                ('icon', models.ImageField(blank=True, upload_to='blog_post_icons/')),
                ('image', models.ImageField(blank=True, upload_to='blog_post_images/')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]