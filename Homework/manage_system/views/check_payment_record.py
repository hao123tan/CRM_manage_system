from django.conf.urls import url
from stark.service.v1 import StarkHandler
from django.shortcuts import redirect,HttpResponse
from manage_system import models


class CheckPaymentRecordHandler(StarkHandler):
    order_list = ['id','confirm_status']
    has_add_btn = None
    list_display = [StarkHandler.display_checkbox,'customer',StarkHandler.get_choice_text('缴费类型','pay_type'),
                    'paid_fee',StarkHandler.get_datetime_text('申请时间','apply_date'),
                    'class_list',StarkHandler.get_choice_text('确认状态','confirm_status'),
                    'consultant']

    def get_urls(self):
        patterns = [
            url(r'list/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            # url(r'add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            # url(r'change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            # url(r'del/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name)
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def multi_confirm(self, request, *args, **kwargs):
        '''
        批量确认
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        pk_list = request.POST.getlist('pk')
        for pk in pk_list:
            payment_object = self.model_class.objects.filter(id=pk,confirm_status=1).first()
            if not payment_object:
                continue
            payment_object.confirm_status = 2
            payment_object.save()

            payment_object.customer.status = 1
            payment_object.customer.save()

            models.Student.objects.filter(customer_id=payment_object.customer.pk).update(student_status=2)
        return redirect(self.reverse_list_url())

    multi_confirm.text = '批量确认'

    def multi_cancel(self, request, *args, **kwargs):
        '''
        批量驳回
        :param request:
        :param args:
        :param kwargs:
        :return:
        '''
        pk_list = request.POST.getlist('pk')
        judge_object = self.model_class.objects.filter(id__in=pk_list,confirm_status=1).update(confirm_status=3)
        print(judge_object)
        if not judge_object:
            return HttpResponse('抱歉 你的之前被确认 已经无法再驳回了')
        return redirect(self.reverse_list_url())

    multi_cancel.text = '批量驳回'

    action_list = [multi_confirm,multi_cancel]