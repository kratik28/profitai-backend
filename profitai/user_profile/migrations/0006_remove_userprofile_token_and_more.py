# Generated by Django 4.2.7 on 2023-11-22 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0005_userprofileotp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='token',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone_number',
            field=models.CharField(blank=True, default=None, max_length=20, null=True, unique=True),
        ),
    ]
