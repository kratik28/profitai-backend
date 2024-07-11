# Generated by Django 5.0.4 on 2024-07-11 16:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        # ('user_profile', '0031_remove_customer_is_purchase'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(blank=True, default=None, null=True)),
                ('vendor_name', models.CharField(max_length=255)),
                ('is_deleted', models.BooleanField(default=False)),
                ('Invoice_pdf', models.FileField(blank=True, null=True, upload_to='request_invoice_pdf/')),
                ('invoice_counter', models.CharField(blank=True, default=None, max_length=30, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('business_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='user_profile.businessprofile')),
            ],
        ),
        migrations.CreateModel(
            name='RequestInvoiceProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255)),
                ('brand', models.CharField(max_length=255)),
                ('qty', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='request_invoices.requestinvoice')),
            ],
        ),
    ]
