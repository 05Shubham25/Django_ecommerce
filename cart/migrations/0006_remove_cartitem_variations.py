# Generated by Django 5.0 on 2025-02-01 20:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0005_cartitem_variations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='variations',
        ),
    ]
