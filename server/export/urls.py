# -*- coding: utf-8 -*-

from django.conf.urls import patterns, url

urlpatterns = patterns(
    'export.views',


    url(r'^$', 'home'),


)
