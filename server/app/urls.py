from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',

    (r'^users/login$', 'tequila.login'),
    (r'^users/logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    url(r'', include('main.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^export/', include('export.urls')),
    url(r'^configs/', include('configs.urls')),
    url(r'^paiements/', include('paiements.urls')),

    (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),  # In prod, use apache !
    (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),  # In prod, use apache !
)
