# Generated by Django 5.0 on 2025-02-04 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_alter_productvariation_unique_together_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variation',
            name='variation_category',
            field=models.CharField(choices=[('marination', 'Marination'), ('cut', 'How to Cut'), ('cleaning', 'Cleaned and Deveined')], max_length=100),
        ),
        migrations.AlterField(
            model_name='variation',
            name='variation_value',
            field=models.CharField(help_text='Select appropriate value based on the category', max_length=100),
        ),
        migrations.AlterUniqueTogether(
            name='variation',
            unique_together={('product', 'variation_category', 'variation_value')},
        ),
    ]
