# Generated by Django 2.2.17 on 2020-12-28 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_auto_20201228_1828'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='following',
            field=models.ManyToManyField(related_name='followers', through='user.Follower', to='user.Profile'),
        ),
    ]