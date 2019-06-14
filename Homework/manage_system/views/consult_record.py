from stark.service.v1 import StarkHandler
from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse
from stark.forms.forms import BootStrapModelForm
from manage_system import models


def New_Record_forms(self, model_class):
    class BasicModelForm(BootStrapModelForm):
        class Meta:
            model = model_class
            fields = ['note', ]

    return BasicModelForm


class ConsultRecordHandler(StarkHandler):
    change_list_template = 'consult_record.html'
    model_form_class = New_Record_forms

    rbac = True

    def display_edit_del(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'
        customer_id = kwargs.get('customer_id')
        tpl = '<a href="%s">编辑</a> <a href="%s">删除</a>' % (
            self.reverse_change_url(pk=obj.pk, customer_id=customer_id),
            self.reverse_delete_url(pk=obj.pk, customer_id=customer_id))
        return mark_safe(tpl)

    def get_urls(self):
        patterns = [
            url(r'list/(?P<customer_id>\d+)/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            url(r'add/(?P<customer_id>\d+)/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'change/(?P<customer_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.change_view),
                name=self.get_change_url_name),
            url(r'del/(?P<customer_id>\d+)/(?P<pk>\d+)/$', self.wrapper(self.delete_view),
                name=self.get_delete_url_name)
        ]
        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def get_queryset(self, request, *args, **kwargs):

        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        return self.model_class.objects.filter(customer_id=customer_id, customer__consultant_id=current_user_id)

    def save(self, request, form, is_update, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        object_exists = models.Customer.objects.filter(id=customer_id, consultant_id=current_user_id).exists()
        if not object_exists:
            return HttpResponse('非法操作')
        if not is_update:
            form.instance.customer_id = customer_id
            form.instance.consultant_id = current_user_id
        form.save()

    def get_change_object(self, request, pk, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        return models.ConsultRecord.objects.filter(pk=pk, customer_id=customer_id,
                                                   customer__consultant_id=current_user_id).first()

    def delete_object(self, request, pk, *args, **kwargs):
        customer_id = kwargs.get('customer_id')
        current_user_id = request.session['user_info']['id']
        record_queryset = models.ConsultRecord.objects.filter(pk=pk, customer_id=customer_id,
                                                              customer__consultant_id=current_user_id)

        if not record_queryset:
            return HttpResponse('要删除的记录不存在，请重新选择')
        record_queryset.delete()

    list_display = ['note', 'consultant', 'date', display_edit_del]
