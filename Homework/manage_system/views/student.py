from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import reverse
from stark.service.v1 import StarkHandler, SearchOption
from stark.forms.forms import BootStrapModelForm


def New_Student_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['qq', 'mobile', 'emergency_contract', 'memo']

    return BasicModelForm


class StudentHandler(StarkHandler):

    def display_score(self, request, obj=None, is_header=None):
        if is_header:
            return '积分管理'
        record_url = reverse('stark:manage_system_scorerecord_list', kwargs={'student_id': obj.pk})
        return mark_safe('<a target = "_blank" href="%s">%s</a>' % (record_url, obj.score))

    list_display = ['customer', 'qq', 'mobile', 'emergency_contract', StarkHandler.get_m2m_text('已报班级', 'class_list'),
                    StarkHandler.get_choice_text('状态', 'student_status'), display_score, StarkHandler.display_edit]
    has_add_btn = None
    model_form_class = New_Student_forms

    def get_urls(self):
        patterns = [
            url(r'list/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            # url(r'add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            # url(r'del/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name)
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    # search_list = ['customer__name','qq__contains','mobile']
    # search_group = [
    #     SearchOption('class_list',text_func=lambda x: '%s-%s'%(x.school.title,x))
    # ]
