from django.conf.urls import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'polybanking.views.home', name='home'),
    # url(r'^polybanking/', include('polybanking.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

    (r'^users/login$', 'tequila.login'),
    (r'^users/logout$', 'django.contrib.auth.views.logout', {'next_page': '/'}),

    url(r'', include('main.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^configs/', include('configs.urls')),
    url(r'^paiements/', include('paiements.urls')),

    (r'^' + settings.MEDIA_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),  # In prod, use apache !
    (r'^' + settings.STATIC_URL[1:] + '(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),  # In prod, use apache !
)
