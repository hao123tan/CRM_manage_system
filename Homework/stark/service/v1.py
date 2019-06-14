from django.conf.urls import url
from django.shortcuts import HttpResponse, render, redirect
from types import FunctionType
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.conf import settings
from stark.utils.pagination import Pagination
from django.http import QueryDict
from stark.forms.forms import Basic_forms
from django.db.models import Q, ForeignKey, ManyToManyField
import functools, datetime


class SearchGroupRow(object):
    def __init__(self, data_list, option, title, query_dict):
        '''

        :param data_list: 组合搜索传入的queryset或者元组
        :param option: 配置
        :param title: 组合搜索的列名称
        :param query_dict: request.GET
        '''
        self.data_list = data_list
        self.option = option
        self.title = title
        self.query_dict = query_dict

    def __iter__(self):
        yield '<div class="whole">'
        yield self.title
        yield '</div>'
        yield '<div class="other">'
        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True

        origin_value_list = self.query_dict.getlist(self.option.field)
        if not origin_value_list:
            yield '<a class="active" href="?%s">全部</a>' % total_query_dict.urlencode()
        else:
            total_query_dict.pop(self.option.field)
            yield '<a href="?%s">全部</a>' % total_query_dict.urlencode()

        for item in self.data_list:
            text = self.option.get_text(item)
            value = self.option.get_value(item)
            query_dict = self.query_dict.copy()
            query_dict._mutable = True
            if not self.option.is_multi:
                query_dict[self.option.field] = value
                if str(value) in origin_value_list:
                    query_dict.pop(self.option.field)
                    yield '<a class="active" href="?%s">%s</a>' % (query_dict.urlencode(), text)
                else:
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)
            else:
                multi_value_list = query_dict.getlist(self.option.field)
                if str(value) in multi_value_list:
                    multi_value_list.remove(str(value))

                    query_dict.setlist(self.option.field, multi_value_list)
                    yield '<a class="active" href="?%s">%s</a>' % (query_dict.urlencode(), text)
                else:

                    multi_value_list.append(str(value))
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)
        yield '</div>'


class SearchOption(object):
    def __init__(self, field, db_condition=None, text_func=None, value_func=None, is_multi=False):
        '''
        :param field:组合搜索关联的字段
        :param db_condition:数据库关联查询时的条件
        :param text_func:搜索结果的中文表达方式 可以自行定义
        :param is_multi:是否支持多选
        '''
        self.field = field
        if not db_condition:
            db_condition = {}
        self.db_condition = db_condition
        self.text_func = text_func
        self.value_func = value_func
        self.is_multi = is_multi
        self.is_choice = False

    def get_db_condition(self, request, *args, **kwargs):
        return self.db_condition

    def get_queryset_or_tuple(self, model_class, request, *args, **kwargs):
        '''
        根据字段去获取数据库关联的数据
        :return:
        '''
        # 根据gender或者depart字符串去model找对象
        field_object = model_class._meta.get_field(self.field)
        title = field_object.verbose_name
        if isinstance(field_object, ForeignKey) or isinstance(field_object, ManyToManyField):
            db_condition = self.get_db_condition(request, *args, **kwargs)
            return SearchGroupRow(field_object.related_model.objects.filter(**db_condition), self, title, request.GET)
        else:
            self.is_choice = True
            return SearchGroupRow(field_object.choices, self, title, request.GET)

    def get_text(self, field_object):
        if self.text_func:
            return self.text_func(field_object)

        if self.is_choice:
            return field_object[1]

        return str(field_object)

    def get_value(self, field_object):
        if self.value_func:
            return self.value_func(field_object)

        if self.is_choice:
            return field_object[0]

        return field_object.pk


class StarkHandler(object):
    change_list_template = None
    add_template = None
    change_template = None
    delete_template = None

    list_display = []

    rbac = False

    has_add_btn = True

    model_form_class = None

    per_page_count = 10

    order_list = []

    search_list = []

    action_list = []

    search_group = []

    def get_list_display(self, request):
        '''
        获取页面上应该显示的列
        :return:
        '''
        value = []
        value.extend(self.list_display)
        if self.rbac:
            value = self.judge_btn(request, value)
        return value

    def get_order_list(self):
        '''
        用于返回排序方法
        :return:
        '''
        return self.order_list or ['-id', ]

    def get_search_list(self):
        '''
        如果search_list中没有值，则不显示input框
        :return:
        '''
        return self.search_list

    def get_action_list(self):
        return self.action_list

    def get_search_group(self):
        return self.search_group

    def get_search_group_condition(self, request):
        '''
        获取组合搜索的条件
        :param request:
        :return:
        '''
        condition = {}
        # 可能这个网页里面会带有大量的param 但是根据option 这里面搜索只用来获取我们需要的要素
        for option in self.search_group:
            if option.is_multi:
                values_list = request.GET.getlist(option.field)  # getlist就是支持多选
                if not values_list:
                    continue
                condition['%s__in' % option.field] = values_list
            else:
                value = request.GET.get(option.field)
                if not value:
                    continue
                condition[option.field] = value
        return condition

    def __init__(self, site, model_class, prev):
        self.site = site
        self.model_class = model_class
        self.prev = prev
        self.request = None

    def get_queryset(self, request, *args, **kwargs):
        return self.model_class.objects

    def changelist(self, request, *args, **kwargs):
        '''
        列表页面
        :param request:
        :return:
        '''
        ############添加搜索条件##########
        search_list = self.get_search_list()
        search_value = request.GET.get('q', '')
        # Q,用于构造负责的ORM查询条件
        conn = Q()
        conn.connector = 'OR'
        if search_value:
            for item in search_list:
                conn.children.append((item, search_value))

        #####获取排序#######
        order_list = self.get_order_list()
        ####获取组合搜索
        search_group_condition = self.get_search_group_condition(request)
        prev_queryset = self.get_queryset(request, *args, **kwargs)
        queryset = prev_queryset.filter(conn).filter(**search_group_condition).order_by(*order_list)
        '''
            根据URL来切片 ?page=3 可能就是30-39这样的
            根据page 来决定索引位置
            生成HTML页码
        '''
        #######处理分页
        all_count = queryset.count()
        query_params = request.GET.copy()
        query_params._mutable = True

        pager = Pagination(
            current_page=request.GET.get('page'),
            all_count=all_count,
            base_url=request.path_info,
            query_params=query_params,
            per_page=self.per_page_count,
        )

        data_list = queryset[pager.start:pager.end]

        #######处理表格
        list_display = self.get_list_display(request)
        header_list = []
        if list_display:
            for key_or_func in list_display:
                if isinstance(key_or_func, FunctionType):
                    verbose_name = key_or_func(self, request, obj=None, is_header=True)
                else:
                    verbose_name = self.model_class._meta.get_field(key_or_func).verbose_name
                header_list.append(verbose_name)
        else:
            header_list.append(self.model_class._meta.model_name)

        body_list = []
        for row in data_list:
            tr_list = []
            if list_display:
                for key_or_func in list_display:
                    if isinstance(key_or_func, FunctionType):
                        tr_list.append(key_or_func(self, request, row, False, *args, **kwargs))
                    else:
                        tr_list.append(getattr(row, key_or_func))
            else:
                tr_list.append(row)
            body_list.append(tr_list)

        #############添加按钮#######
        add_btn = self.get_add_btn(request, *args, **kwargs)

        #############处理Action#####
        action_list = self.get_action_list()
        action_dict = {func.__name__: func.text for func in action_list}

        if request.method == 'POST':
            action_func_name = request.POST.get('action')
            if action_func_name and action_func_name in action_dict:
                action_response = getattr(self, action_func_name)(request, *args, **kwargs)
                if action_response:
                    return action_response

        ###############处理组合搜索########
        search_group_row_list = []
        search_group = self.get_search_group()
        for option_object in search_group:
            row = option_object.get_queryset_or_tuple(self.model_class, request, *args, **kwargs)
            search_group_row_list.append(row)
        return render(request, self.change_list_template or 'stark/changelist.html', {'data_list': data_list,
                                                                                      'header_list': header_list,
                                                                                      'body_list': body_list,
                                                                                      'pager': pager,
                                                                                      'add_btn': add_btn,
                                                                                      'search_list': search_list,
                                                                                      'search_value': search_value,
                                                                                      'action_dict': action_dict,
                                                                                      'search_group_row_list': search_group_row_list})

    def get_add_btn(self, request, *args, **kwargs):
        if self.rbac:
            self.has_add_btn = self.judge_btn(request, None)
        if self.has_add_btn:
            add_url = self.reverse_add_url(*args, **kwargs)
            return '<a class="btn btn-primary" href="%s">添加</a>' % add_url
        return None

    def Basic_Forms(self, model_class, add_or_change, request, pk, *args, **kwargs):
        '''
        用于添加Forms的组件分配
        :param model_class:
        :return:
        '''
        if not self.model_form_class:
            return Basic_forms(model_class)
        else:
            return self.model_form_class(model_class)

    def save(self, request, form, is_update, *args, **kwargs):
        '''
        预留了save函数 自定义操作 可以在外面的自定义的Userinfohandle里面进行重写 保存的时候自动默认存储没有设置的值
        :param form:form就是传导进来的存储的值
        :param is_update:
        :return:
        '''
        # 这个可以设置想要存到底是什么值 如果自定义一些框没有显示 就是默认这些框的值按照某种方法存储 这种情况下 就要重写save进行存储
        # form.instance.depart_id = 1
        form.save()

    def add_view(self, request, *args, **kwargs):
        '''
        添加页面
        :param request:
        :return:
        '''
        basic_forms = self.Basic_Forms(self.model_class, 'add', request, None, *args, **kwargs)
        if request.method == 'GET':
            form = basic_forms()
            return render(request, self.add_template or 'stark/change.html', {'form': form})
        form = basic_forms(data=request.POST)
        if form.is_valid():
            response = self.save(request, form, False, *args, **kwargs)
            # 在数据库保存成功后，跳转回列表页面(携带了原来的页面)
            list_url = self.reverse_list_url(*args, **kwargs)
            return response or redirect(list_url)
        return render(request, self.add_template or 'stark/change.html', {'form': form})

    def get_change_object(self, request, pk, *args, **kwargs):
        return self.model_class.objects.filter(pk=pk).first()

    def change_view(self, request, pk, *args, **kwargs):
        '''
        编辑页面
        :param request:
        :return:
        '''
        current_obj = self.get_change_object(request, pk, *args, **kwargs)
        if not current_obj:
            return HttpResponse('你要的数据不存在,请重新输入')

        basic_forms = self.Basic_Forms(self.model_class, 'change', request, pk, *args, **kwargs)
        if request.method == 'GET':
            form = basic_forms(instance=current_obj)
            return render(request, self.change_template or 'stark/change.html', {'form': form})
        form = basic_forms(data=request.POST, instance=current_obj)
        if form.is_valid():
            response = self.save(request, form, True, *args, **kwargs)
            # 在数据库保存成功后，跳转回列表页面(携带了原来的页面)
            list_url = self.reverse_list_url(*args, **kwargs)
            return response or redirect(list_url)
        return render(request, self.change_template or 'stark/change.html', {'form': form})

    def delete_object(self, request, pk, *args, **kwargs):
        '''
        可重写的删除
        :param request:
        :param pk:
        :param args:
        :param kwargs:
        :return:
        '''
        self.model_class.objects.filter(pk=pk).delete()

    def delete_view(self, request, pk, *args, **kwargs):
        '''
        删除页面
        :param request:
        :return:
        '''
        origin_list_url = self.reverse_list_url(*args, **kwargs)
        if request.method == 'GET':
            return render(request, self.delete_template or 'stark/delete.html', {'cancel': origin_list_url})
        response = self.delete_object(request, pk, *args, **kwargs)
        return response or redirect(origin_list_url)

    def multi_delete(self, request, *args, **kwargs):
        '''
        批量删除(如果想要定制执行成功后的返回值，那么就为action制定返回值)
        :return:
        '''
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(id__in=pk_list).delete()

    multi_delete.text = '批量删除'

    def get_url_name(self, param):
        '''
        生成URL的name
        :param param:传入的URL里面功能性描述的词汇
        :return:
        '''
        app_label, model_name = self.model_class._meta.app_label, self.model_class._meta.model_name
        if self.prev:
            return '%s_%s_%s_%s' % (app_label, model_name, self.prev, param)
        return '%s_%s_%s' % (app_label, model_name, param)

    @property
    def get_list_url_name(self):
        '''
        获取列表页面URL的name
        :return:
        '''
        return self.get_url_name('list')

    @property
    def get_add_url_name(self):
        '''
        获取添加页面URL的name
        :return:
        '''
        return self.get_url_name('add')

    @property
    def get_change_url_name(self):
        '''
        获取编辑页面URL的name
        :return:
        '''
        return self.get_url_name('change')

    @property
    def get_delete_url_name(self):
        '''
        获取删除页面URL的name
        :return:
        '''
        return self.get_url_name('del')

    def reverse_commons_url(self, name, *args, **kwargs):
        name = "%s:%s" % (self.site.namespace, name)
        base_url = reverse(name, args=args, kwargs=kwargs)
        if not self.request.GET:
            change_url = base_url
        else:
            param = self.request.GET.urlencode()
            new_query_dict = QueryDict(mutable=True)
            new_query_dict['_filter'] = param
            change_url = '%s?%s' % (base_url, new_query_dict.urlencode())
        return change_url

    def reverse_add_url(self, *args, **kwargs):
        '''
        生成带有原搜索条件的添加URL
        :return:
        '''
        return self.reverse_commons_url(self.get_add_url_name, *args, **kwargs)

    def reverse_change_url(self, *args, **kwargs):
        '''
        生成带有原搜索条件的编辑URL
        :param args:
        :param kwargs:
        :return:
        '''
        return self.reverse_commons_url(self.get_change_url_name, *args, **kwargs)

    def reverse_delete_url(self, *args, **kwargs):
        '''
        生成带有原搜索条件的删除URL
        :param args:
        :param kwargs:
        :return:
        '''
        return self.reverse_commons_url(self.get_delete_url_name, *args, **kwargs)

    def reverse_list_url(self, *args, **kwargs):
        name = "%s:%s" % (self.site.namespace, self.get_list_url_name)
        base_url = reverse(name, args=args, kwargs=kwargs)
        param = self.request.GET.get('_filter')
        if not param:
            list_url = base_url
        else:
            list_url = '%s?%s' % (base_url, param)
        return list_url

    def wrapper(self, func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)

        return inner

    def get_urls(self):
        patterns = [
            url(r'list/$', self.wrapper(self.changelist), name=self.get_list_url_name),
            url(r'add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'change/(?P<pk>\d+)/$', self.wrapper(self.change_view), name=self.get_change_url_name),
            url(r'del/(?P<pk>\d+)/$', self.wrapper(self.delete_view), name=self.get_delete_url_name)
        ]

        patterns.extend(self.extra_urls())  # 这个self并不是这个基类的self 而是最开始从传入的那个handler开始寻找有没有extra_urls
        return patterns

    def extra_urls(self):
        return []

    def display_checkbox(self, request, obj=None, is_header=None, *args, **kwargs):
        '''
        自定义显示的函数
        :param obj: 传入的obj 用于生成表格内容 详情可以看v1里面的表格obj生成程序
        :param is_header: 表头
        :return:
        '''
        if is_header:
            return '选择'
        return mark_safe('<input type="checkbox" name="pk" value="%s">' % obj.pk)

    def display_edit(self, request, obj=None, is_header=None, *args, **kwargs):
        '''
        自定义显示的函数
        :param obj: 传入的obj 用于生成表格内容 详情可以看v1里面的表格obj生成程序
        :param is_header: 表头
        :return:
        '''
        if is_header:
            return '编辑操作'
        change_url = self.reverse_change_url(pk=obj.pk)
        return mark_safe('<a href="%s">编辑</a>' % change_url)

    def display_del(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '删除操作'
        delete_url = self.reverse_delete_url(pk=obj.pk)
        return mark_safe('<a href="%s">删除</a>' % delete_url)

    def display_edit_del(self, request, obj=None, is_header=None, *args, **kwargs):
        if is_header:
            return '操作'
        tpl = '<a href="%s">编辑</a> <a href="%s">删除</a>' % (
            self.reverse_change_url(pk=obj.pk), self.reverse_delete_url(pk=obj.pk))
        return mark_safe(tpl)

    def get_choice_text(title, field):
        '''
        stark组件显示带有choice的情况下 使用这个函数 传入表头和元素名称
        :param field:
        :return:
        '''

        def inner(self, request, obj=None, is_header=None, *args, **kwargs):
            if is_header:
                return title
            method = 'get_%s_display' % field
            return getattr(obj, method)()

        return inner

    def get_datetime_text(title, field, format='%Y-%m-%d'):
        '''
        stark组件显示带有choice的情况下 使用这个函数 传入表头和元素名称
        :param field:
        :return:
        '''

        def inner(self, request, obj=None, is_header=None, *args, **kwargs):
            if is_header:
                return title
            datatime_value = getattr(obj, field)
            return datatime_value.strftime(format)

        return inner

    def get_m2m_text(title, field):
        '''
        stark组件显示带有choice的情况下 使用这个函数 传入表头和元素名称
        :param field:
        :return:
        '''

        def inner(self, request, obj=None, is_header=None, *args, **kwargs):
            if is_header:
                return title
            queryset = getattr(obj, field).all()
            text_list = [str(row) for row in queryset]
            return ','.join(text_list)

        return inner

    def judge_btn(self, request, list):
        permission_dict = request.session.get(settings.PERMISSION_SESSION_KEY)
        if not list:
            if self.get_add_url_name in permission_dict:
                return True
            return False
        else:
            if self.get_change_url_name and self.get_delete_url_name in permission_dict:
                list.append(type(self).display_edit_del)
            elif self.get_change_url_name in permission_dict:
                list.append(type(self).display_edit)
            elif self.get_delete_url_name in permission_dict:
                list.append(type(self).display_del)
            return list


class StarkSite(object):
    def __init__(self):
        self._registry = []
        self.app_name = 'stark'
        self.namespace = 'stark'

    def register(self, model_class, handler_class=None, prev=None):
        '''

        :param model_class: model中的数据库相关的类
        :param handlerclass: 处理请求的视图函数所在的类
        :param prev: 生成URL的前缀
        :return:
        '''
        if not handler_class:
            handler_class = StarkHandler
        self._registry.append(
            {'model_class': model_class, 'handler': handler_class(self, model_class, prev), 'prev': prev})

    def get_urls(self):

        patterns = []
        for item in self._registry:
            model_class = item['model_class']
            handler = item['handler']
            prev = item['prev']
            app_label, model_name = model_class._meta.app_label, model_class._meta.model_name

            if prev:
                # 进行再分发
                patterns.append(url(r'%s/%s/%s/' % (app_label, model_name, prev), (handler.get_urls(), None, None)))
            else:

                patterns.append(url(r'%s/%s/' % (app_label, model_name), (handler.get_urls(), None, None)))
        return patterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = StarkSite()
