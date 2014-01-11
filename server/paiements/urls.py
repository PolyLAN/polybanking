# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'paiements.views',

    url(r'^start/$', 'start'),
    url(r'^go/(?P<pk>[0-9]+)$', 'go'),
    url(r'^ipn$', 'ipn'),
    url(r'^return$', 'return_from_postfinance'),

    url(r'^transactions/list$', 'transactions_list'),
    url(r'^transactions/(?P<pk>[0-9]+)/$', 'transactions_show'),
    url(r'^transactions/(?P<pk>[0-9]+)/logs$', 'transactions_show_logs'),
    url(r'^transactions/(?P<pk>[0-9]+)/ipn$', 'transactions_send_ipn'),
   

)
