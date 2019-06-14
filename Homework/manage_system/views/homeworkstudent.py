from stark.service.v1 import StarkHandler
from django.conf.urls import url
from django.shortcuts import render, reverse, HttpResponse, redirect
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.conf import settings
from manage_system import models
from stark.forms.forms import BootStrapModelForm
import os


class BasicModelForm(BootStrapModelForm):
    class Meta:
        model = models.HomeWorkStudentRecord
        fields = ['homework', 'avatar']


class HomeworkStudentHandler(StarkHandler):
    change_template = 'homework_submit.html'
    has_add_btn = None

    def display_submit(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '作业提交'
        current_user_id = request.session['user_info']['id']
        course_record_obj = models.HomeWorkStudentRecord.objects.filter(pk=obj.pk, student_id=current_user_id).get()
        name = '%s:%s' % (self.site.namespace, self.get_url_name('homeworksubmit'))
        attendance_url = reverse(name, kwargs={'course_record_id': course_record_obj.course_record_id, 'pk': obj.pk})
        tpl = '<a target="_blank" href="%s">作业提交</a>' % attendance_url
        return mark_safe(tpl)

    def display_homeworkview(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '作业查看'
        current_user_id = request.session['user_info']['id']
        course_record_obj = models.HomeWorkStudentRecord.objects.filter(pk=obj.pk, student_id=current_user_id).get()
        name = '%s:%s' % (self.site.namespace, self.get_url_name('homeworkview'))
        attendance_url = reverse(name, kwargs={'course_record_id': course_record_obj.course_record_id})
        tpl = '<a target="_blank" href="%s">作业</a>' % attendance_url
        return mark_safe(tpl)

    list_display = ['student', 'course_record', display_homeworkview, display_submit]

    def get_urls(self):
        patterns = [
            url(r'list/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            # url(r'add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            # url(r'change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            # url(r'del/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
            url(r'homeworkview/(?P<course_record_id>\d+)/$', self.wrapper(self.homework_view),
                name=self.get_url_name('homeworkview')),
            url(r'submit/(?P<course_record_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.homework_submit),
                name=self.get_url_name('homeworksubmit')),
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def get_queryset(self, request, *args, **kwargs):
        # request.session['user_info']['id']
        current_user_id = request.session['user_info']['id']
        return self.model_class.objects.filter(student_id=current_user_id)

    def get_change_object(self, request, pk, *args, **kwargs):
        course_record_id = kwargs.get('course_record_id')
        current_user_id = request.session['user_info']['id']
        return self.model_class.objects.filter(pk=pk, course_record_id=course_record_id,
                                               student_id=current_user_id).first()

    def homework_submit(self, request, pk, *args, **kwargs):
        current_user_id = request.session['user_info']['id']
        course_record_id = kwargs.get('course_record_id')
        current_obj = self.get_change_object(request, pk, *args, **kwargs)
        if not current_obj:
            return HttpResponse('你要的数据不存在,请重新输入')

        basic_forms = BasicModelForm
        if request.is_ajax():
            response = {'user': None, 'msg': None}
            homework = request.POST.get('homework')
            avatar_obj = request.FILES.get('avatar')
            if not avatar_obj:
                response['msg'] = '抱歉！你的文件没有获取'
                return JsonResponse(response)
            file_path = os.path.join(settings.MEDIA_ROOT, 'avatars', avatar_obj.name)
            print(file_path)
            f = open(file_path, 'wb')
            for chunk in avatar_obj.chunks():
                f.write(chunk)
            f.close()
            models.HomeWorkStudentRecord.objects.filter(student_id=current_user_id,
                                                        course_record_id=course_record_id).update(homework=homework,
                                                                                                  avatar=file_path)
            url_name = '%s:%s' % (self.site.namespace, self.get_list_url_name)
            return redirect(url_name)
        form = basic_forms(instance=current_obj)
        return render(request, self.change_template or 'stark/change.html', {'form': form})

    def homework_view(self, request, *args, **kwargs):
        course_record_id = kwargs.get('course_record_id')
        homework_list = models.CourseRecord.objects.filter(pk=course_record_id)
        return render(request, 'homework_view.html', {'homework_list': homework_list})
