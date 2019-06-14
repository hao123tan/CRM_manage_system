from django.shortcuts import render,redirect
from manage_system import models
from manage_system.utils.md5 import gen_md5
from rbac.service.init_permission import init_permission

def login(request):
    if request.method == 'GET':
        return render(request,'login.html')

    user = request.POST.get('username')
    pwd = gen_md5(request.POST.get('password',''))

    user_object = models.UserInfo.objects.filter(name=user,password=pwd).first()
    if not user_object:
        return render(request,'login.html',{'error':'用户名或者密码错误'})
    request.session['user_info'] = {'id':user_object.id,'nickname':user_object.nickname}

    init_permission(user_object,request)
    return redirect('/index/')


def logout(request):
    request.session.delete()
    return redirect('/login/')

def index(request):
    return render(request,'index.html')