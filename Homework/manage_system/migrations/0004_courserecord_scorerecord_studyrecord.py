# Generated by Django 2.1.5 on 2019-06-05 14:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manage_system', '0003_paymentrecord'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_num', models.IntegerField(verbose_name='节次')),
                ('date', models.DateField(auto_now_add=True, verbose_name='上课日期')),
                ('homework_title', models.CharField(blank=True, max_length=64, null=True, verbose_name='作业标题')),
                ('homework_memo', models.TextField(blank=True, null=True, verbose_name='作业描述')),
                ('exam', models.TextField(blank=True, null=True, verbose_name='踩分点')),
                ('class_object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manage_system.Classlist', verbose_name='班级')),
                ('teacher', models.ForeignKey(limit_choices_to={'depart__title': '教职部'}, on_delete=django.db.models.deletion.CASCADE, to='manage_system.UserInfo', verbose_name='讲师')),
            ],
        ),
        migrations.CreateModel(
            name='ScoreRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='评分理由')),
                ('score', models.IntegerField(help_text='最终得分', verbose_name='分值')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manage_system.Student', verbose_name='学生')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manage_system.UserInfo', verbose_name='执行人')),
            ],
        ),
        migrations.CreateModel(
            name='StudyRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record', models.CharField(choices=[('checked', '已签到'), ('vacate', '请假'), ('late', '迟到'), ('noshow', '缺勤'), ('leave_early', '早退')], default='checked', max_length=64, verbose_name='上课记录')),
                ('course_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manage_system.CourseRecord', verbose_name='第几天课程')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manage_system.Student', verbose_name='学员')),
            ],
        ),
    ]
