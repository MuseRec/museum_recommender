# Generated by Django 3.1.1 on 2020-09-08 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('museum_site', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdemographic',
            name='education',
            field=models.CharField(choices=[('none-high-school', 'Less than high school'), ('high-school', 'High School'), ('college', 'College (no degree)'), ('bachelors', "Bachelor's"), ('masters', "Master's"), ('phd', 'Doctorate')], max_length=16),
        ),
    ]
