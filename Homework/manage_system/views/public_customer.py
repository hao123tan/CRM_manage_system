from django.utils.safestring import mark_safe
from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from django.db import transaction
from django.conf import settings
from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm
from manage_system import models


def New_Public_Customer_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            exclude = ['consultant']

    return BasicModelForm


class PublicCustomerHandler(StarkHandler):

    def display_record(self,request, obj=None, is_header=None):
        if is_header:
            return '跟进记录'
        record_url = self.reverse_record_url(pk=obj.pk)

        return mark_safe('<a target="_blank" href="%s">查看跟进</a>' % record_url)

    list_display = [StarkHandler.display_checkbox, 'name', 'qq', StarkHandler.get_choice_text('状态', 'status'),
                    StarkHandler.get_m2m_text('咨询课程', 'course'), display_record]

    def get_queryset(self, request, *args, **kwargs):
        return self.model_class.objects.filter(consultant__isnull=True)

    model_form_class = New_Public_Customer_forms

    @property
    def get_record_url_name(self):
        return self.get_url_name('record_view')

    def reverse_record_url(self, *args, **kwargs):
        '''
        生成带有原搜索条件的跟进记录的URL
        :param args:
        :param kwargs:
        :return:
        '''
        return self.reverse_commons_url(self.get_record_url_name, *args, **kwargs)

    def extra_urls(self):
        patterns = [
            url(r'^record/(?P<pk>\d+)/$', self.wrapper(self.record_view), name=self.get_record_url_name)
        ]
        return patterns

    def record_view(self, request, pk):
        '''
        查看跟进记录
        :param request:
        :param pk:
        :return:
        '''
        record_list = models.ConsultRecord.objects.filter(customer_id=pk)
        return render(request, 'record_view.html', {'record_list': record_list})

    def multi_apply(self, request, *args, **kwargs):
        '''
        申请到私户(如果想要定制执行成功后的返回值，那么就为action制定返回值 意思就是有一个返回值话 就会执行返回值 比如跳转到百度页面)
        :return:
        '''
        current_user_id = request.session['user_info']['id']
        pk_list = request.POST.getlist('pk')

        private_customer_count = models.Customer.objects.filter(consultant_id=current_user_id, status=2).count()
        if (private_customer_count + len(pk_list)) > models.Customer.MAX_PRIVATE_CUSTOMER_COUNT:
            return HttpResponse('做人不要太贪心了，你的账户里面已经有了%s个，你还能申请到私户的学员有%s'% (
            private_customer_count, models.Customer.MAX_PRIVATE_CUSTOMER_COUNT - private_customer_count))

        flag = False
        with transaction.atomic():#事务
            #在数据库中加锁
            origin_queryset = models.Customer.objects.filter(id__in=pk_list, status=2, consultant__isnull=True).select_for_update()
            if len(origin_queryset) == len(pk_list):
                models.Customer.objects.filter(id__in=pk_list, status=2, consultant__isnull=True).update(consultant_id=current_user_id)
                flag = True
                return redirect(self.reverse_list_url())
        if not flag:
            return HttpResponse('手速太慢，选中的客户已被其他人申请，请重新选择')



    multi_apply.text = '批量添加到私户'

    action_list = [multi_apply, ]
