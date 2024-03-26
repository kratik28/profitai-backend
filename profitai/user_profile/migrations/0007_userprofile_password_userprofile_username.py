# Generated by Django 4.2.7 on 2023-11-23 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0006_remove_userprofile_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='password',
            field=models.CharField(default=None, max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='username',
            field=models.CharField(default=None, max_length=150, unique=True),
            preserve_default=False,
        ),
    ]
