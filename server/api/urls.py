# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'api.views',


    url(r'^transactions/$', 'transactions_list'),

    url(r'^transactions/(?P<reference>.*)/logs/$', 'transactions_show_logs'),
    url(r'^transactions/(?P<reference>.*)/$', 'transactions_show'),

)
