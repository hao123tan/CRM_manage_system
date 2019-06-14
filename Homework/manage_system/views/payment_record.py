from django.conf.urls import url
from django.shortcuts import HttpResponse
from django import forms
from stark.service.v1 import StarkHandler
from stark.forms.forms import BootStrapModelForm
from manage_system import models


def New_PaymentRecord_forms(self, model_class,add_or_change, request, pk, *args, **kwargs):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['pay_type', 'paid_fee', 'class_list', 'note']

    return BasicModelForm


def New_StudentPaymentRecord_forms(self, model_class,add_or_change, request, pk, *args, **kwargs):
    class BasicModelForm(BootStrapModelForm):
        qq = forms.CharField(label='QQ号', max_length=32)
        mobile = forms.CharField(label='电话号码', max_length=32)
        emergency_contract = forms.CharField(label='紧急联系号码', max_length=32)

        class Meta:
            model = model_class
            fields = ['pay_type', 'paid_fee', 'class_list', 'qq', 'mobile', 'emergency_contract', 'note']

    return BasicModelForm


class PaymentRecordHandler(StarkHandler):
    model_form_class = New_PaymentRecord_forms
    list_display = [StarkHandler.get_choice_text('费用类型', 'pay_type'), 'consultant', 'paid_fee', 'class_list',
                    StarkHandler.get_choice_text('状态', 'confirm_status')]

    def get_urls(self):
        patterns = [
            url(r'list/(?P<customer_id>\d+)/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            url(r'add/(?P<customer_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
        ]
        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def get_queryset(self, request, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        return self.model_class.objects.filter(customer_id=customer_id, customer__consultant_id=current_user_id)

    def Basic_Forms(self, model_class, add_or_change, request, pk, *args, **kwargs):
    # 如果当前客户有学生信息，则使用PaymentRecordModelForm；否则StudentPaymentRecordModelForm
        customer_id = kwargs.get('customer_id')
        student_exists = models.Student.objects.filter(customer_id=customer_id).exists()
        if not student_exists:
            return New_StudentPaymentRecord_forms(self,model_class,add_or_change, request, pk, *args, **kwargs)
        return New_PaymentRecord_forms(self,model_class,add_or_change, request, pk, *args, **kwargs)

    def save(self, request, form, is_update, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        object_exists = models.Customer.objects.filter(id=customer_id, consultant_id=current_user_id).exists()
        if not object_exists:
            return HttpResponse('非法操作')

        form.instance.customer_id = customer_id
        form.instance.consultant_id = current_user_id
        form.save()

        #创建学员信息
        class_list = form.cleaned_data['class_list']
        fetch_student_object = models.Student.objects.filter(customer_id=customer_id).first()
        if not fetch_student_object:
            qq = form.cleaned_data['qq']
            mobile = form.cleaned_data['mobile']
            emergency_contract = form.cleaned_data['emergency_contract']
            student_object = models.Student.objects.create(customer_id=customer_id,qq=qq,mobile=mobile,emergency_contract=emergency_contract)
            student_object.class_list.add(class_list.id)
        else:
            fetch_student_object.class_list.add(class_list.id)
