# Generated by Django 5.0 on 2025-01-04 17:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0012_remove_order_selected_timing_slot'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='status',
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('NotCompleted', 'NotCompleted')], default='Pending', max_length=20),
        ),
    ]
