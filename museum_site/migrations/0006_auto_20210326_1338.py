# Generated by Django 3.1.1 on 2021-03-26 13:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('museum_site', '0005_artworkvisited_rating'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artworkvisited',
            name='rating',
            field=models.IntegerField(null=True),
        ),
    ]