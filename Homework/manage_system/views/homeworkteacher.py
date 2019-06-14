from stark.service.v1 import StarkHandler
from django.conf.urls import url
from django.utils.safestring import mark_safe
from stark.forms.forms import BootStrapModelForm


def New_Homework_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['homework_title', 'homework_memo', 'exam']

    return BasicModelForm


class HomeWorkTeacherHandler(StarkHandler):
    has_add_btn = False

    def display_edit(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'
        course_record_id = kwargs.get('course_record_id')
        tpl = '<a href="%s">编辑</a>' % (self.reverse_change_url(pk=obj.pk, course_record_id=course_record_id))
        return mark_safe(tpl)

    list_display = ['day_num', 'homework_title', 'homework_memo', 'exam', display_edit]
    model_form_class = New_Homework_forms

    def get_urls(self):
        patterns = [
            url(r'list/(?P<course_record_id>\d+)/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            # url(r'add/(?P<course_record_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'change/(?P<course_record_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.change_view),
                name=self.get_change_url_name),
            # url(r'del/(?P<course_record_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name),
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def get_queryset(self, request, *args, **kwargs):
        course_record_id = kwargs.get('course_record_id')
        return self.model_class.objects.filter(pk=course_record_id)
