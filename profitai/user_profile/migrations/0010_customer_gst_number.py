# Generated by Django 4.2.7 on 2023-12-08 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0009_alter_userprofile_options_alter_userprofile_managers_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='gst_number',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
    ]
