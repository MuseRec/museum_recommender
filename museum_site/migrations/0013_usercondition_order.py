# Generated by Django 3.1.1 on 2022-03-04 16:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('museum_site', '0012_usercondition'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercondition',
            name='order',
            field=models.CharField(default='test', max_length=6),
            preserve_default=False,
        ),
    ]