from django.utils.safestring import mark_safe
from django.urls import reverse
from django.shortcuts import redirect
from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm


def New_private_Customer_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            exclude = ['consultant']

    return BasicModelForm


class PrivateCustomerHandler(StarkHandler):

    def display_record(self, request, obj=None, is_header=None):
        if is_header:
            return '跟进记录'
        record_url = reverse('stark:manage_system_consultrecord_list', kwargs={'customer_id': obj.pk})
        return mark_safe('<a target="blank" href="%s">查看跟进</a>' % record_url)

    def display_pay_record(self, request, obj=None, is_header=None):
        if is_header:
            return '缴费记录'
        record_url = reverse('stark:manage_system_paymentrecord_list', kwargs={'customer_id': obj.pk})
        return mark_safe('<a target="blank" href="%s">缴费</a>' % record_url)

    model_form_class = New_private_Customer_forms
    list_display = [StarkHandler.display_checkbox, 'name', 'qq', StarkHandler.get_choice_text('状态', 'status'),
                    StarkHandler.get_m2m_text('咨询课程', 'course'), display_pay_record, display_record]

    def get_queryset(self, request, *args, **kwargs):
        # request.session['user_info']['id']
        current_user_id = request.session['user_info']['id']
        return self.model_class.objects.filter(consultant_id=current_user_id)

    def save(self, request, form, is_update, *args, **kwargs):
        if not is_update:
            current_user_id = request.session['user_info']['id']
            form.instance.consultant_id = current_user_id
        form.save()

    def multi_remove(self, request, *args, **kwargs):
        '''
        移除到公户(如果想要定制执行成功后的返回值，那么就为action制定返回值 意思就是有一个返回值话 就会执行返回值 比如跳转到百度页面)
        :return:
        '''
        current_user_id = request.session['user_info']['id']
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(id__in=pk_list, consultant_id=current_user_id).update(consultant=None)
        return redirect(self.reverse_list_url())

    multi_remove.text = '移除到公户'

    action_list = [multi_remove, ]
