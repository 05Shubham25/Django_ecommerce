# Generated by Django 5.0 on 2025-02-01 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0017_ordervariation_variation_value'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ordervariation',
            name='order_product',
        ),
        migrations.RemoveField(
            model_name='ordervariation',
            name='variation_value',
        ),
    ]
