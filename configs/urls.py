# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'configs.views',

    url(r'^$', 'list'),
    url(r'^(?P<pk>[0-9]?)/show/$', 'show'),
    url(r'^(?P<pk>[0-9]?)/edit/$', 'edit'),
    url(r'^(?P<pk>[0-9]?)/logs/$', 'show_logs'),
    
    #url(r'^(?P<pk>[0-9]?)/delete/$', 'delete'),

    url(r'^(?P<pk>[0-9]?)/keys/ipn/new/$', 'new_ipn_key'),
    url(r'^(?P<pk>[0-9]?)/keys/requests/new/$', 'new_requests_key'),
    url(r'^(?P<pk>[0-9]?)/keys/api/new/$', 'new_api_key'),

)
