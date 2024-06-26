# Generated by Django 4.2.8 on 2023-12-15 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0011_customer_favourite'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='businessprofile',
            name='address_and_zipcode',
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='address1',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='address2',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='city',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='state',
            field=models.CharField(blank=True, default=None, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='businessprofile',
            name='zipcode',
            field=models.CharField(blank=True, default=None, max_length=10, null=True),
        ),
    ]
