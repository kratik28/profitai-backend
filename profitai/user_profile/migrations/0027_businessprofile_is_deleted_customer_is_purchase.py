# Generated by Django 5.0.4 on 2024-05-17 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0026_businessprofile_other_business_type_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessprofile',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='is_purchase',
            field=models.BooleanField(default=False),
        ),
    ]