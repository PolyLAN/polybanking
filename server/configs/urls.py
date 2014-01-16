# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'configs.views',

    url(r'^$', 'list'),
    url(r'^(?P<pk>[0-9]+)/show/$', 'show'),
    url(r'^(?P<pk>[0-9]+)/edit/$', 'edit'),
    url(r'^(?P<pk>[0-9]+)/logs/$', 'show_logs'),

    #url(r'^(?P<pk>[0-9]+)/delete/$', 'delete'),

    url(r'^(?P<pk>[0-9]+)/keys/(?P<key_type>(ipn|requests|api))/new/$', 'new_ipn_key'),

)
