# Generated by Django 5.0 on 2025-01-04 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0013_remove_payment_status_payment_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='order_number',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
