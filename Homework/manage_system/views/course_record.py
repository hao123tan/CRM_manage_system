from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse, render
from django.urls import reverse
from django.forms.models import modelformset_factory
from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm
from manage_system import models


def New_CourseRecord_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['day_num', 'teacher', 'homework_title', 'homework_memo', 'exam']

    return BasicModelForm


class New_StudyRecord_forms(BootStrapModelForm):
    class Meta:
        model = models.StudyRecord
        fields = ['record', ]


class New_HomeWorkScore_forms(BootStrapModelForm):
    class Meta:
        model = models.HomeWorkStudentRecord
        fields = ['score', ]


class CourseRecordHandler(StarkHandler):
    model_form_class = New_CourseRecord_forms

    def display_edit_del(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'
        class_id = kwargs.get('class_id')
        tpl = '<a href="%s">编辑</a> <a href="%s">删除</a>' % (
            self.reverse_change_url(pk=obj.pk, class_id=class_id),
            self.reverse_delete_url(pk=obj.pk, class_id=class_id))
        return mark_safe(tpl)

    def display_attendance(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '考勤'
        name = '%s:%s' % (self.site.namespace, self.get_url_name('attendance'))
        attendance_url = reverse(name, kwargs={'course_record_id': obj.pk})
        tpl = '<a target="_blank" href="%s">考勤</a>' % attendance_url
        return mark_safe(tpl)

    def display_homework(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '作业'
        homework_url = reverse('stark:manage_system_courserecord_homework_list', kwargs={'course_record_id': obj.pk})
        return mark_safe('<a target="_blank" href="%s">作业发布</a>' % homework_url)

    def display_homeworkscore(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '作业批改'
        name = '%s:%s' % (self.site.namespace, self.get_url_name('homeworkscore'))
        attendance_url = reverse(name, kwargs={'course_record_id': obj.pk})
        tpl = '<a target="_blank" href="%s">作业批改</a>' % attendance_url
        return mark_safe(tpl)

    list_display = [StarkHandler.display_checkbox, 'class_object', 'day_num', 'teacher',
                    StarkHandler.get_datetime_text('日期', 'date'), display_homework, display_attendance,
                    display_homeworkscore, display_edit_del]

    def get_urls(self):
        patterns = [
            url(r'list/(?P<class_id>\d+)/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            url(r'add/(?P<class_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'change/(?P<class_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.change_view),
                name=self.get_change_url_name),
            url(r'del/(?P<class_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
            url(r'attendance/(?P<course_record_id>\d+)/$', self.wrapper(self.attendance_view),
                name=self.get_url_name('attendance')),
            url(r'homeworkscore/(?P<course_record_id>\d+)/$', self.wrapper(self.homework_view),
                name=self.get_url_name('homeworkscore')),
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def get_queryset(self, request, *args, **kwargs):
        class_id = kwargs.get('class_id')
        return self.model_class.objects.filter(class_object_id=class_id)

    def save(self, request, form, is_update, *args, **kwargs):
        class_id = kwargs.get('class_id')
        if not is_update:
            form.instance.class_object_id = class_id
        form.save()

    def multi_init(self, request, *args, **kwargs):
        course_record_id_list = request.POST.getlist('pk')
        class_id = kwargs.get('class_id')
        class_object = models.Classlist.objects.filter(id=class_id).first()
        if not class_object:
            return HttpResponse('班级不存在')
        student_object_all = class_object.student_set.all()

        for course_record_id in course_record_id_list:
            course_record_object = models.CourseRecord.objects.filter(id=course_record_id,
                                                                      class_object_id=class_id).first()

            if not course_record_object:
                continue

            # 判断此上课记录的考勤记录是否已经存在
            study_record_exists = models.StudyRecord.objects.filter(course_record=course_record_object).exists()
            if study_record_exists:
                continue

            # 为每个学生在该天创造考勤记录
            study_record_object_list = [models.StudyRecord(student_id=stu.id, course_record_id=course_record_id)
                                        for stu in student_object_all]
            models.StudyRecord.objects.bulk_create(study_record_object_list, batch_size=50)

    def multi_init_homework(self, request, *args, **kwargs):
        course_record_id_list = request.POST.getlist('pk')
        class_id = kwargs.get('class_id')
        class_object = models.Classlist.objects.filter(id=class_id).first()
        if not class_object:
            return HttpResponse('班级不存在')
        student_object_all = class_object.student_set.all()

        for course_record_id in course_record_id_list:
            course_record_object = models.CourseRecord.objects.filter(id=course_record_id,
                                                                      class_object_id=class_id).first()

            if not course_record_object:
                continue

            # 判断此上课记录的作业记录是否已经存在
            study_record_exists = models.HomeWorkStudentRecord.objects.filter(
                course_record=course_record_object).exists()
            if study_record_exists:
                continue

            # 为每个学生在该天创造作业记录
            study_record_object_list = [
                models.HomeWorkStudentRecord(student_id=stu.id, course_record_id=course_record_id)
                for stu in student_object_all]
            models.HomeWorkStudentRecord.objects.bulk_create(study_record_object_list, batch_size=50)

    def attendance_view(self, request, course_record_id, *args, **kwargs):
        '''
        考勤的批量操作
        :param request:
        :param course_record_id:
        :param args:
        :param kwargs:
        :return:
        '''
        study_record_object_list = models.StudyRecord.objects.filter(course_record_id=course_record_id)
        study_model_formset = modelformset_factory(models.StudyRecord, New_StudyRecord_forms, extra=0)
        if request.method == 'POST':
            formset = study_model_formset(queryset=study_record_object_list, data=request.POST)
            if formset.is_valid():
                formset.save()
            return render(request, 'attendance.html', {'formset': formset})
        formset = study_model_formset(queryset=study_record_object_list)
        return render(request, 'attendance.html', {'formset': formset})

    def homework_view(self, request, course_record_id, *args, **kwargs):
        '''
        作业的批量操作
        :param request:
        :param course_record_id:
        :param args:
        :param kwargs:
        :return:
        '''
        homework_score_object_list = models.HomeWorkStudentRecord.objects.filter(course_record_id=course_record_id)
        homework_score_formset = modelformset_factory(models.HomeWorkStudentRecord, New_HomeWorkScore_forms, extra=0)
        if request.method == 'POST':
            formset = homework_score_formset(queryset=homework_score_object_list, data=request.POST)
            if formset.is_valid():
                formset.save()
            return render(request, 'HomeworkScore.html', {'formset': formset})
        formset = homework_score_formset(queryset=homework_score_object_list)
        return render(request, 'HomeworkScore.html', {'formset': formset})

    multi_init.text = '批量初始化考勤'
    multi_init_homework.text = '批量初始化作业'

    action_list = [multi_init, multi_init_homework, ]
