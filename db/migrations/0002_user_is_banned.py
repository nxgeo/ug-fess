# Generated by Django 5.1.2 on 2024-10-20 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("db", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_banned",
            field=models.BooleanField(default=False),
        ),
    ]
