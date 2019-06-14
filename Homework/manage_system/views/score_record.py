from django.conf.urls import url
from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm

def New_ScoreRecord_forms(self,model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['content','score']

    return BasicModelForm


class ScoreRecordHandler(StarkHandler):
    list_display = ['content','score' ,'user']
    model_form_class = New_ScoreRecord_forms

    def get_urls(self):
        patterns = [
            url(r'list/(?P<student_id>\d+)/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            url(r'add/(?P<student_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            # url(r'change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            # url(r'del/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name)
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def save(self, request, form, is_update, *args, **kwargs):
        student_id = kwargs.get('student_id')
        current_user_id = request.session['user_info']['id']

        form.instance.student_id = student_id
        form.instance.user_id = current_user_id
        form.save()

        form.instance.student.score += form.instance.score
        form.instance.student.save()
