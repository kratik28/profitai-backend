# Generated by Django 4.2.7 on 2023-11-08 10:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_menu', '0001_initial'),
        ('user_profile', '0002_userprofile_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_number', models.CharField(blank=True, default=None, max_length=20, null=True)),
                ('business_name', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('gst_number', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('address_and_zipcode', models.CharField(default=None, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_menu.businesstype')),
                ('industry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_menu.industry')),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.userprofile')),
            ],
        ),
    ]
