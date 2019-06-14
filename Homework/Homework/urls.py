"""Homework URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.views.static import serve
from django.conf import settings
from django.conf.urls import url, include
from stark.service.v1 import site
from manage_system.views import account
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^stark/', site.urls),
    url(r'media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^rbac/', include(('rbac.urls', 'rbac'), namespace='rbac')),
    url(r'^login/', account.login,name='login'),
    url(r'^logout/', account.logout,name='logout'),
    url(r'^index/', account.index,name='index'),
]
