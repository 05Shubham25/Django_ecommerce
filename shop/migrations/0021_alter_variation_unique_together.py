# Generated by Django 5.0 on 2025-02-04 17:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0020_alter_variation_variation_value'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='variation',
            unique_together=set(),
        ),
    ]
