# Generated by Django 5.0 on 2024-04-29 13:02

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_alter_orderproduct_payment'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimingSlot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slot', models.CharField(choices=[('pre_order', 'Pre order - 9-11am'), ('morning_delivery', 'Morning orders delivered by 12-1pm'), ('evening_slot', 'Evening slot 7-9pm')], max_length=20)),
            ],
        ),
        migrations.AddField(
            model_name='order',
            name='timing_slot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orders.timingslot'),
        ),
    ]
