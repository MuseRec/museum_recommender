# Generated by Django 3.1.1 on 2022-02-17 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommendations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datarepresentation',
            name='source',
            field=models.CharField(max_length=12),
        ),
    ]