from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from stark.service.v1 import site, StarkHandler, SearchOption
from stark.forms.forms import BootStrapModelForm, StarkForm
from manage_system.utils.md5 import gen_md5
from manage_system import models


def New_add_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        confirm_password = forms.CharField(label='确认密码')

        class Meta:
            model = model_class
            fields = ['name', 'password', 'confirm_password', 'nickname', 'gender', 'phone', 'email', 'depart', 'roles']

        def clean_confirm_password(self):
            password = self.cleaned_data['password']
            confirm_password = self.cleaned_data['confirm_password']
            if password != confirm_password:
                raise ValidationError('密码输入不一致')
            return confirm_password

        def clean(self):
            password = self.cleaned_data['password']
            self.cleaned_data['password'] = gen_md5(password)
            return self.cleaned_data

    return BasicModelForm


def New_change_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['name', 'nickname', 'gender', 'phone', 'email', 'depart', 'roles']

    return BasicModelForm


class ResetPasswordForm(StarkForm):
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='确认密码', widget=forms.PasswordInput)

    def clean_confirm_password(self):
        password = self.cleaned_data['password']
        confirm_password = self.cleaned_data['confirm_password']
        if password != confirm_password:
            raise ValidationError('密码输入不一致')
        return confirm_password

    def clean(self):
        password = self.cleaned_data['password']
        self.cleaned_data['password'] = gen_md5(password)
        return self.cleaned_data


class UserInfoHandler(StarkHandler):

    # search_list = ['nickname__contains','name__contains']
    # search_group = [
    #     SearchOption(field='gender'),
    #     SearchOption(field='depart')
    # ]

    def display_reset(self, request, obj=None, is_header=None):
        if is_header:
            return '重置密码'
        reset_url = self.reverse_reset_pwd_url(pk=obj.pk)
        return mark_safe('<a href="%s">重置密码</a>' % reset_url)

    list_display = ['nickname', StarkHandler.get_choice_text('性别', 'gender'), 'phone', 'email', 'depart', display_reset,
                    StarkHandler.display_edit_del]

    def Basic_Forms(self, model_class, add_or_change, request, pk, *args, **kwargs):
        if add_or_change == 'add':
            return New_add_forms(self, model_class)
        elif add_or_change == 'change':
            return New_change_forms(self, model_class)

    def reset_password(self, request, pk):
        '''
        重置密码页面
        :param request:
        :param pk:
        :return:
        '''
        User_obj = models.UserInfo.objects.filter(id=pk).first()
        if not User_obj:
            return HttpResponse('用户不存在')
        form = ResetPasswordForm()
        if request.method == 'GET':
            return render(request, 'stark/change.html', {'form': form})
        form = ResetPasswordForm(data=request.POST)
        if form.is_valid():
            # 密码更新到数据库
            User_obj.password = form.cleaned_data['password']
            User_obj.save()
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    @property
    def get_reset_pwd_url_name(self):
        return self.get_url_name('reset_pwd')

    def reverse_reset_pwd_url(self, *args, **kwargs):
        '''
        生成带有原搜索条件的重置密码URL
        :param args:
        :param kwargs:
        :return:
        '''
        return self.reverse_commons_url(self.get_reset_pwd_url_name, *args, **kwargs)

    def extra_urls(self):
        patterns = [
            url(r'^reset/password/(?P<pk>\d+)/$', self.wrapper(self.reset_password), name=self.get_reset_pwd_url_name)
        ]
        return patterns
