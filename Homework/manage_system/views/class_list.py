from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm
from stark.forms.widgets import DateTimePickerInput
from django.utils.safestring import mark_safe
from django.shortcuts import reverse


def New_datetime_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = '__all__'
            widgets = {
                'start_date': DateTimePickerInput,
                'graduate_date': DateTimePickerInput
            }

    return BasicModelForm


class ClassListHandler(StarkHandler):
    def display_course(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '班级'
        return '%s(%s)期' % (obj.course.name, obj.semester)

    def display_course_record(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '上课记录'
        record_url = reverse('stark:manage_system_courserecord_normal_list', kwargs={'class_id': obj.pk})
        return mark_safe('<a target = "_blank" href="%s">上课记录</a>' % record_url)

    model_form_class = New_datetime_forms

    list_display = ['school', StarkHandler.get_datetime_text('开班日期', 'start_date'),
                    StarkHandler.get_m2m_text('任课老师', 'tech_teacher'), display_course, display_course_record,
                    StarkHandler.display_edit_del]
