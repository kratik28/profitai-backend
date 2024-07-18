# Generated by Django 5.0.4 on 2024-07-18 16:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '__first__'),
        ('user_profile', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_counter', models.CharField(blank=True, default=None, max_length=30, null=True)),
                ('order_date_time', models.DateTimeField(blank=True, default=None, null=True)),
                ('status', models.IntegerField(blank=True, default=None, null=True)),
                ('grand_total', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('sub_total', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('paid_amount', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('remaining_total', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('tax', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('discount', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('payment_option', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('payment_type', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('description', models.TextField(blank=True, default=None, max_length=100, null=True)),
                ('Invoice_pdf', models.FileField(blank=True, null=True, upload_to='invoice_pdf/')),
                ('ewaybill_number', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_purchase', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.businessprofile')),
                ('customer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_profile.customer')),
                ('vendor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user_profile.vendor')),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(blank=True, default=None, null=True)),
                ('deal_quantity', models.IntegerField(blank=True, default=None, null=True)),
                ('price', models.DecimalField(blank=True, decimal_places=2, default=None, max_digits=10, null=True)),
                ('packaging', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('batch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.batches')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.invoice')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.product')),
            ],
        ),
    ]