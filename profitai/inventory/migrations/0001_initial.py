# Generated by Django 4.2.7 on 2023-11-08 12:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_profile', '0005_userprofileotp'),
        ('master_menu', '0002_brand_producttype_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(default=None, max_length=50)),
                ('quantity', models.IntegerField(blank=True, default=None, null=True)),
                ('sales_price', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('purchase_price', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('tax', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('discount', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('status', models.IntegerField(blank=True, default=None, null=True)),
                ('expiry_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_menu.brand')),
                ('business_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.businessprofile')),
                ('product_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_menu.producttype')),
                ('size', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='master_menu.size')),
            ],
        ),
    ]
