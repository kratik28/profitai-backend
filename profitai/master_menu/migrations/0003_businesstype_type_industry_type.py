# Generated by Django 4.2.8 on 2024-02-06 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('master_menu', '0002_brand_producttype_size'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesstype',
            name='type',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='industry',
            name='type',
            field=models.CharField(blank=True, default=None, max_length=50, null=True),
        ),
    ]
