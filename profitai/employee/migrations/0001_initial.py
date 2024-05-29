# Generated by Django 5.0.4 on 2024-05-29 17:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_profile', '0028_remove_customer_is_purchase_vendor'),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('contact_number', models.CharField(max_length=15)),
                ('location', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('role', models.CharField(max_length=50)),
                ('date_of_joining', models.DateField()),
                ('salary', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employees', to='user_profile.businessprofile')),
            ],
        ),
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('check_in_time', models.TimeField()),
                ('check_out_time', models.TimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Present', 'Present'), ('Absent', 'Absent'), ('Leave', 'Leave')], default='Present', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='user_profile.businessprofile')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='employee.employee')),
            ],
        ),
    ]
