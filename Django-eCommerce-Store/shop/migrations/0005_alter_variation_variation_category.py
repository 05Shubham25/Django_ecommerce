# Generated by Django 4.1.5 on 2024-03-15 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_alter_variation_variation_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('masala', 'Masala'), ('size', 'size')], max_length=100),
        ),
    ]
