# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'users.views',

    url(r'^$', 'list'),
    url(r'^(?P<pk>[0-9]+)/show/$', 'show'),
    url(r'^(?P<pk>[0-9]+)/edit/$', 'edit'),
    url(r'^(?P<pk>[0-9]+)/delete/$', 'delete'),

)
