# Generated by Django 3.1.1 on 2022-03-02 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('museum_site', '0010_domainknowledge'),
    ]

    operations = [
        migrations.AddField(
            model_name='userdemographic',
            name='disability',
            field=models.CharField(choices=[('disable', 'Identify as disabled'), ('not disabled', 'Do not identify as disable'), ('no answer', 'Prefer not to answer')], default='default', max_length=20),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='domainknowledge',
            name='art_knowledge',
            field=models.CharField(choices=[('novice', 'Novice'), ('some', 'I have got some knowledge'), ('knowledgeable', 'Knowledgeable'), ('expert', 'Expert')], max_length=20),
        ),
    ]
