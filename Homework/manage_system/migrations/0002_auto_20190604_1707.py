# Generated by Django 2.1.5 on 2019-06-04 17:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manage_system', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classlist',
            name='tech_teacher',
            field=models.ManyToManyField(blank=True, limit_choices_to={'depart__title': '教学部'}, related_name='teach_classes', to='manage_system.UserInfo', verbose_name='任课老师'),
        ),
    ]